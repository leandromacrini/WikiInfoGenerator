import requests
from bs4 import BeautifulSoup
import re
import os
import csv
import argparse
from datetime import date, datetime
import dateparser

headers = {'User-Agent': 'WikiInfoGenerator/1.0 (https://www.bolognanerd.it; amministrazione@bolognanerd.it)'}

def fetch_wiki_table(item_name):
	wikipedia_url = f"https://it.wikipedia.org/api/rest_v1/page/html/{item_name}"
	response = requests.get(wikipedia_url, headers=headers)
	soup = BeautifulSoup(response.text, 'html.parser')

	#rimuovi le note wiki
	for sup in soup.find_all('sup'): sup.clear()
	for nop in soup.find_all(class_="noprint"): nop.clear()

	table = soup.find('table', {'class': 'infobox'})
	if table is None:
		print(f"La tabella non è stata trovata per '{item_name}'.")
		return None


	item_info = {}
	
	#tipo di dispositivo
	item_type = table.find(class_="sinottico_sottotitolo").text
	item_info["Nome"] = table.find(class_="sinottico_testata").th.next_element
	
	#la descrizione è tutto il testo della prima section
	item_info["Descrizione"] = '\n\n'.join([x.text for x in soup.section.find_all("p")])
	item_info["URL"] = wikipedia_url

	central_images = table.find_all(class_="sinottico_testo_centrale")

	if (len(central_images) > 0):
		srcset = central_images[0].a.img.get('srcset')
		logo_images = srcset.split() if srcset else None
		if(logo_images and len(logo_images) > 0):
			item_info["Logo"] = re.sub('\s.+', '', logo_images[-2]).replace('//','https://')
		else: 
			item_info["Logo"] = table.find_all(class_="sinottico_testo_centrale")[0].a.img.attrs['src'].replace('//','https://')
		
		#get best version
		if('thumb'in item_info['Logo']):
			item_info['Logo'] = os.path.split(item_info['Logo'])[0].replace('thumb/','')

	if (len(central_images) > 1):
		srcset = central_images[1].a.img.get('srcset')
		foto_images = srcset.split() if srcset else None
		if(foto_images and len(foto_images) > 0):
			item_info["Foto"] = re.sub('\s.+', '', foto_images[-2]).replace('//','https://')
		else: 
			item_info["Foto"] = table.find_all(class_="sinottico_testo_centrale")[1].a.img.attrs['src'].replace('//','https://')
		
		#get best version
		item_info['Foto'] = os.path.split(item_info['Foto'])[0].replace('thumb/','')

	if (item_type == "console"):
		for row in table.tbody.find_all('tr', recursive=False):
			if( not row.th):
				continue
			elif(row.th.text == "Produttore"):
				item_info["Produttore"] = row.td.text.strip()
			elif(row.th.text == "Generazione"):
				item_info["Generazione"] = row.td.text.strip()
			elif(row.th.text == "Dismissione"):
				item_info["Dismissione"] = row.td.text.strip()
			elif(row.th.text == "Gioco più diffuso"):
				item_info["Gioco più diffuso"] = row.td.text.strip()
			elif(row.th.text == "Supporto dimemoria"):
				item_info["Supporto di memoria"] ='\n'.join([a.text.strip() for a in row.td.find_all('a')])
			elif(row.th.text == "Dispositividi controllo"):
				item_info["Dispositivi di controllo"] = '\n'.join([a.text.strip() for a in row.td.find_all('a')])
			elif(row.th.text == "CPU"):
				item_info["CPU"] = row.td.text.strip()
			elif(row.th.text == "RAM totale"):
				item_info["RAM totale"] = row.td.text.strip()
			elif(row.th.text == "GPU"):
				item_info["GPU"] = row.td.text.strip()
			elif(row.th.text == "Unità vendute"):
				item_info["Unita vendute"] = row.td.contents[0].replace('\xa0','')
			elif(row.th.text == "In vendita"):
				item_info["Rilasci"] = []
				new_item = {}
				new_item['Data'] = ''
				new_item['Flag'] = None

				#only one date or year
				if (len(row.td.contents) == 2):
					new_item['Data'] = row.td.a.text.strip()
					item_info["Rilasci"].append(new_item)
				else:
					for element in row.td.contents:

						if(element.name == 'span' and element.attrs.get('style') != 'font-size:90%' and element.a and element.a.img):
							flag_images = element.a.img.attrs['srcset'].split(', ')
							if(len(flag_images) > 0):
								new_item["Flag"] = re.sub('\s.+', '', flag_images[-1]).replace('//','https://')
							else: 
								new_item["Flag"] = element.a.img.attrs['src'].replace('//','https://')

							#get best version
							new_item['Flag'] = os.path.split(new_item['Flag'])[0].replace('thumb/','')

						elif(element.name == 'br' or element.text == '\n'):
							new_item['Data'] = new_item['Data'].strip()
							item_info["Rilasci"].append(new_item)

							#reset new_item
							new_item = {}
							new_item['Data'] = ''
							new_item['Flag'] = None
							continue

						#read the text (next cycle will add the item at the next "br" element)
						else:
							new_item['Data'] += element.text

	elif (item_type == "computer"):
		a=2#TODO

	#Release Year
	item_info["Anno di rilascio"] = None
	if(item_info.get('Rilasci') and len(item_info.get('Rilasci')) > 0):
		item_info["Anno di rilascio"] = sorted([ dateparser.parse(x['Data']) or datetime.now() for x in item_info['Rilasci']])[0].year

	return item_info

def generate_csv(input_file, output_file):
	# Leggi i nomi di console da un file di testo
	print(f"Leggo il file {input_file}...")
	with open(input_file, 'r') as f:
		console_names = f.read().splitlines()

	print(f"Sono state trovati {len(console_names)} elementi da cercare...")
	# Per ogni nome di console, genera le informazioni sull'oggetto
	item_infos = []
	for item_name in console_names:
		print(f"Recupero i dati da wikipedia per {item_name}...")
		item_info = fetch_wiki_table(item_name)

		if item_info:
			item_infos.append(item_info)

	# Scrivi le informazioni sull'oggetto in un file CSV
	print(f"Scrivo il risultato nel file {output_file}...")
	all_fields = set().union(*item_infos)
	with open(output_file, 'w', newline='', encoding='utf-8') as f:
		writer = csv.DictWriter(f, fieldnames=all_fields, delimiter=";")
		writer.writeheader()
	
		for item_info in item_infos:
			writer.writerow(item_info)
	
	print(f"Completato.")

if __name__ == "__main__":
   parser = argparse.ArgumentParser(description='Genera un file CSV con le informazioni sulle console.')
   parser.add_argument('input_file', help='Il file di input con i nomi delle console.')
   parser.add_argument('output_file', help='Il file di output CSV.')
   args = parser.parse_args()

   generate_csv(args.input_file, args.output_file)
