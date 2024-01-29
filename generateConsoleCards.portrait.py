import requests
from PIL import Image, ImageDraw, ImageFont
from  Drawtable2 import Drawtable2
import io
import os
import cairosvg
import qrcode
import qrcode.image.svg
import csv
import argparse


headers = {'User-Agent': 'WikiInfoGenerator/1.0 (https://www.bolognanerd.it; amministrazione@bolognanerd.it)'}

def download_image(url):
	data = None
	if(os.path.exists(url)):
		with open(url, "r") as file:
			# Reading from a file
			data = file.read()
	else:
		response = requests.get(url, headers=headers, stream=True)
		if response.status_code == 200:
			data = response.content
		
	if(os.path.splitext(url)[-1] == ".svg"):
		out = io.BytesIO()
		try:
			cairosvg.svg2png(bytestring=data, write_to=out)
			return Image.open(out)
		except Exception as ex:
			return None
	else:
		data = io.BytesIO(data)
		return Image.open(data)
	
	return None

def draw_multiline_textbox(bg_image, string, font: ImageFont.FreeTypeFont, x, y, width, height, color='black', edge=False, h_align="center", v_align="center", debug =False):
	draw = ImageDraw.Draw(bg_image, "RGBA")

	if(debug == True):
		draw.rectangle((x,y,x+width, y+height))

	multilines = string.split('\n')
	lines = []
	for multiline in multilines:
		words = multiline.split()
		length = len(words)
		start = 0
		for i in range(length+1):
			line = ' '.join(words[start:i+1])
			w = font.getlength(line)
			if (w > width):
				lines.append(' '.join(words[start:i]))
				start = i
			elif i == length:
				lines.append(line)
		lines[-1] += "\n"

	len_lines = len(lines)
	start_y = y

	if(v_align=="center"):
		start_y = y + (height - (len_lines * font.size))/2
	if(v_align=="bottom"):
		start_y = y + (height - (len_lines * font.size))

	dy = (font.size + font.size/4)
	for i, line in enumerate(lines):
		if edge and (line[-1] != '\n'):
			words = line.split()
			total_difference = width - font.getlength(''.join(words))
			delta = total_difference / (len(words)-1)
			x_temp = x

			for j, word in enumerate(words):
				draw.text((x_temp, start_y+i*dy), word, fill=color, font=font)
				x_temp += font.getlength(word)+delta
		else:
			_, _, w, h = draw.textbbox((0, 0), line, font=font)

			if(h_align == "left"):
				draw.text((x, start_y+i*dy), line, fill=color, font=font)
			elif(h_align == "center"):
				draw.text((x+(width-w)/2, start_y+i*dy), line, fill=color, font=font)
			elif(h_align == "right"):
				draw.text((x+width-w, start_y+i*dy), line, fill=color, font=font)
			
			
def create_item_card(item_info, output_path="item_card.png"):

	# create online missing cards (to reprint remove original file)
	if(os.path.exists(output_path)):
		print(f"Immagine {output_path} già presente, la escludo.")
		return

	#CARD parameters
	text_color = "black"
	card_color= "white"
	font_size = 18*3
	# width = 1180 + 1180/2
	card_width, card_height = 1240, 1748
	card = Image.new("RGBA", (card_width, card_height), color=card_color)

	# TITLE
	title_width, title_height = int(card_width*2/3), card_height

	draw = ImageDraw.Draw(card)

	# Caricamento del font
	font_path = "ZenKakuGothicAntique-Regular.ttf"
	font_bold_path="ZenKakuGothicAntique-Medium.ttf"
	font = ImageFont.truetype(font_path, font_size* 4/6)
	font_big = ImageFont.truetype(font_path, font_size)
	font_small = ImageFont.truetype(font_path, font_size*3/5)
	font_bold = ImageFont.truetype(font_bold_path, font_size* 4/6)
	font_big_bold = ImageFont.truetype(font_bold_path, font_size * 4/3)

	gap = int(font_size/2)

	#Nome
	nome_anno = f"{item_info['Nome']} ({item_info['Anno di rilascio']})"
	draw_multiline_textbox(card, nome_anno, font_big_bold, gap, gap, title_width - 2*gap, title_height * 1/7 - 2*gap, color=text_color, h_align="left", v_align="top")

	#Descrizione
	draw_multiline_textbox(card, item_info['Descrizione'], font, gap, title_height*1/7, title_width - 2*gap, title_height*3/5, color=text_color, edge=True, h_align="left", v_align="top")

	#Proprietario
	prop = f"Dalla collezione di: {item_info['Proprietario']}"
	draw_multiline_textbox(card, prop, font_small, gap, title_height*4/5 - font_small.size - gap, title_width - 2*gap, title_height*4/5, color=text_color, h_align="left", v_align="top")


	#Lines
	#draw.line([(gap, title_height*1/5 +gap),(title_width-gap, title_height*1/5 +gap)], fill=text_color, width=2)
	draw.line([(gap, title_height*4/5),(card_width-gap, title_height*4/5)], fill=text_color, width=2)
	draw.line([(title_width, gap),(title_width, title_height* 4/5 - gap)], fill=text_color, width=2)

	#Logo
	if(item_info["Logo"]):
		image = download_image(item_info["Logo"])
		if image is not None:
			image = image.convert("RGBA")
			image.thumbnail((( card_width/2 - 2*gap ), title_height * 1/5 - 2*gap), Image.Resampling.LANCZOS)
			card.alpha_composite(image, (gap, int(title_height*4/5 + (title_height*1/5 - image.height)/2)))


	#QRCode URL
	qrcode_size = 200
	qr = qrcode.QRCode(
		version=1,
		box_size=7,
		border=0,
		error_correction=qrcode.constants.ERROR_CORRECT_L
	)
	qr.add_data(item_info["URL"])
	qr.make()
	qr_img = qr.make_image(fill_color=text_color)
	qr_img = qr_img.convert("RGBA")
	#card.paste(qr_img, (card_width-qr_img.width-gap, card_height-qr_img.height-3*gap), qr_img)

	#FonteWiki
	draw_multiline_textbox( 
		card, "(2024) Wikipedia", font_small,
		card_width-qr_img.width-gap, card_height-qr_img.height-4*gap,
		qr_img.width, gap,
		color=text_color, v_align="center", h_align="center",
		debug=True
	)

	#INFO TABLE
	table_width, table_height = int(card_width*1/3) - 2*gap, int(card_height * 4/5 - 2*gap)

	# Creazione di un'immagine vuota
	table_img = Image.new("RGBA", (table_width, table_height), color=card_color)

	tdata = []

	if(item_info['Produttore']):
		tdata.append(['Produttore'])
		tdata.append([item_info['Produttore']])
		tdata.append([' '])

	if(item_info['Generazione']):
		tdata.append(['Generazione'])
		tdata.append([item_info['Generazione']])
		tdata.append([' '])


	if(item_info['Anno di rilascio']):
		from_to_sell = f"Dal {item_info['Anno di rilascio']}"
		
		if(item_info['Dismissione']):
			from_to_sell += f" al {item_info['Dismissione']}"

		tdata.append(['In vendita'])
		tdata.append([from_to_sell])
		tdata.append([' '])

	if(item_info['Unita vendute']):
		tdata.append(['Unità vendute'])
		tdata.append([item_info['Unita vendute']])
		tdata.append([' '])
	
	if(item_info['CPU']):
		tdata.append(['Processore'])
		tdata.append([item_info['CPU']])
		tdata.append([' '])

	if(item_info['RAM totale']):
		tdata.append(['RAM'])
		tdata.append([item_info['RAM totale']])
		tdata.append([' '])
	
	if(item_info['GPU']):
		tdata.append(['GPU'])
		tdata.append([item_info['GPU']])
		tdata.append([' '])

	if(item_info['Supporto di memoria']):
		tdata.append(['Supporti'])
		tdata.append([item_info['Supporto di memoria']])
		tdata.append([' '])

	if(item_info['Dispositivi di controllo']):
		tdata.append(['Controller'])
		tdata.append([item_info['Dispositivi di controllo']])
		tdata.append([' '])

	if(item_info['Gioco più diffuso']):
		tdata.append(['Bestseller'])
		tdata.append([item_info['Gioco più diffuso']])
		tdata.append([' '])

	if(len(tdata) > 0):
		table = Drawtable2(data=tdata,
			x= 0,
			xend= table_width,
			y= gap,
			font=font,
			line_spacer=10,
			margin_text=0,
			image_width=table_width,
			image_height=table_height,
			frame=False,
			grid=False,
			columngrid=False,
			rowgrid=False,
			header=False,
			text_color=text_color,
			drawsheet= table_img,
			return_params=True,
			first_column_header = False,
			headerfont=font_bold,
			alternate_bold = 3

		)
		start_x,start_y,end_x,end_y = table.draw_table()

		card.paste(table_img, (int(card_width*2/3) + gap, gap))

	card.save(output_path)
	print(f"Immagine creata con successo: {output_path}")
	return

	y_position = gap
	for key, value in item_info.items():
		
		if(key == "Rilasci"):
			draw.text((gap, y_position), f"{key}:", fill=text_color, font=font)
			y_position += gap
			for rilascio in value:
				image = download_image(rilascio['Flag'])
				image = image.convert("RGBA")
				image.thumbnail((gap*2,gap*2), Image.Resampling.LANCZOS)
				img.paste(image, (gap*3, y_position+gap), image)
				draw.text((gap*5 + image.width, y_position+gap), f"{rilascio['Data']}", fill=text_color, font=font)
				y_position += image.height + gap
		else:
			text = f"{key}: {value}"
			draw.text((gap, y_position), text, fill=text_color, font=font)
			y_position += gap

	# Salvataggio dell'immagine
	img.save(output_path)
	print(f"Immagine creata con successo: {output_path}")

def generate_cards(input_file):
   # Leggi le informazioni sull'oggetto da un file CSV
   with open(input_file, 'r', encoding='utf-8') as f:
       reader = csv.DictReader(f, delimiter=";")
       item_infos = list(reader)

   # Per ogni informazione sull'oggetto, genera una carta dell'oggetto
   for item_info in item_infos:
       output_path = f"cards-portrait/{item_info['Nome'].replace('/','-')}_card.png"
       create_item_card(item_info, output_path)

if __name__ == "__main__":
   parser = argparse.ArgumentParser(description='Genera le card delle console a partire da un file CSV.')
   parser.add_argument('input_file', help='Il file di input CSV con le informazioni sulle console.')
   args = parser.parse_args()

   generate_cards(args.input_file)


