from datetime import datetime
import mysql.connector
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import re

from bs4 import BeautifulSoup    


def RasparLista(livros):
    
    options = Options()
    #options.add_argument("--headless")  # Executar o Chrome em modo headless (sem interface gráfica)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36")
    service = Service("D:\Downloads\chromedriver-win64\chromedriver.exe")  # Caminho para o executável do ChromeDriver
    driver = webdriver.Chrome(service=service, options=options)

    
    for livro in livros:
        url = "https://www.magazineluiza.com.br/busca/"+ livro['isbn10']

        driver.get(url)
        time.sleep(7)
        data = driver.page_source
        soup = BeautifulSoup(data, 'html.parser')
        cards = soup.find_all('li', class_=["sc-kTbCBX ciMFyT"] )

        livrosRaspados = []
        i = 0
        titulo = livro['titulo']
        titulo_sem_caracteres = re.split(r'[:,.\\/()-]', titulo)
        tres_primeiras_palavras = ' '.join(titulo_sem_caracteres[0].split()[:3])

        titulo_quebrado = [tres_primeiras_palavras] + titulo_sem_caracteres[1:]

        if len(cards)<1:
            print("Livro não encontrado: " + livro['titulo'])
        else:
            for card in cards:
                if i >= 10:
                    break 
                
                if card is not None:
                    titulo_magalu = card.find('h2', class_=["sc-fvwjDU fbccdO"]).text.strip()
                    
                    if str(titulo_quebrado[0].lower()) in titulo_magalu.lower():
                        i+=1
                        preco = card.find('p', class_=["sc-kpDqfm efxPhd sc-gEkIjz jmNQlo"])
                        link = card.find('a', class_=["sc-eBMEME uPWog sc-cDnByv dgyHCD sc-cDnByv dgyHCD"])
                        link_text = "https://www.magazineluiza.com.br/" + link['href']
                        
                        img = card.find('img', class_=["sc-cWSHoV bLJsBf"])
                        img_src = img['src']

                        preco_text = "0.0"
                        if preco is not None:
                            preco_match = re.search(r"R\$\s*(\d+,\d+)", preco.text.strip())
                            preco_text = preco_match.group(1) if preco_match else "Preço não disponível"
                            preco_text = preco_text.replace(',', '.')

                        livro_raspado = {
                            'IdLivro': livro['id'],
                            'IdCapa': livro['capa'],
                            'Titulo Banco': titulo,
                            'Link Img': img_src,
                            'Isbn10': livro['isbn10'],
                            'Isbn13': re.sub(r'[-.]', '', livro['isbn13']),
                            'Autor Banco': livro['autor'],
                            'Link Magalu': link_text,
                            'Preco Magalu': preco_text,
                            'Titulo Magalu': titulo_magalu
                        }

                        print(link_text)
                        livrosRaspados.append(livro_raspado)            
                    
                    
            #livrosValidos = ConfirmarLivroInfo(livrosRaspados);
            print("Livros validos 1")
            for livroRaspado in livrosRaspados:
                print("Id do Livro:", livroRaspado['IdLivro'])
                print("Capa:", livroRaspado['IdCapa'])
                print("Título no Banco:", livroRaspado['Titulo Banco'])
                print("ISBN-10:", livroRaspado['Isbn10'])
                print("ISBN-13:", livroRaspado['Isbn13'])
                print("Autor no Banco:", livroRaspado['Autor Banco'])
                print("Link Img:", livroRaspado['Link Img'])
                print("Link Magalu:", livroRaspado['Link Magalu'])
                print("Preço Magalu:", livroRaspado['Preco Magalu'])
                print("Título Magalu:", livroRaspado['Titulo Magalu'])
                print("--------------------")  


        if len(livrosRaspados) > 0:
            handleLivroValido(livrosRaspados);
      

    driver.quit()   
    return "ok"


def handleLivroValido(livrosValidos):

    db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="serpabooksdb"
    )       

    cursor = db.cursor()

    livro_menor_preco = min(livrosValidos, key=lambda livro: float(livro['Preco Magalu']))

    livro_menor_preco['Data cadastro'] = datetime.now()

    print("\nLivro com o menor preço:")
    print("Id do Livro:", livro_menor_preco['IdLivro'])
    print("Capa:", livro_menor_preco['IdCapa'])
    print("Título no Banco:", livro_menor_preco['Titulo Banco'])
    print("ISBN-10:", livro_menor_preco['Isbn10'])
    print("Autor no Banco:", livro_menor_preco['Autor Banco'])
    print("Link Img:", livro_menor_preco['Link Img'])
    print("Link Magalu:", livro_menor_preco['Link Magalu'])
    print("Preço Magalu:", livro_menor_preco['Preco Magalu'])
    print("Título Magalu:", livro_menor_preco['Titulo Magalu'])
    print("Data cadastro:", livro_menor_preco['Data cadastro'])
    print("--------------------")


    sql = "SELECT * FROM preco_magalu pm WHERE pm.id_livro = %s "   
    val = (livro_menor_preco['IdLivro'],)
    cursor.execute(sql, val)
    resultado = cursor.fetchall()
    

    if(resultado):
        print("aqui")
        idPrecoMagalu = resultado[0][0]
        sql = "UPDATE preco_magalu SET preco_magalu = %s, link_magalu = %s, img_magalu = %s, dt_cadastro_preco_magalu = %s WHERE id_preco_magalu = %s"
        val = (livro_menor_preco['Preco Magalu'], livro_menor_preco['Link Magalu'], livro_menor_preco['Link Img'], livro_menor_preco['Data cadastro'], idPrecoMagalu,)
        cursor.execute(sql, val)
        db.commit()
        return "ok";
    
    sql = "INSERT INTO preco_magalu (link_magalu, img_magalu, preco_magalu, dt_cadastro_preco_magalu, id_livro ) VALUES (%s, %s, %s, %s, %s)"
    val = (livro_menor_preco['Link Magalu'], livro_menor_preco['Link Img'], livro_menor_preco['Preco Magalu'], livro_menor_preco['Data cadastro'], livro_menor_preco['IdLivro'],)
    cursor.execute(sql, val)
    db.commit()

    return "ok";

def scrapper():

    db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="serpabooksdb"
    )       

    cursor = db.cursor()

    #sql = "SELECT l.id_livro, l.titulo_livro, l.id_capa, l.url_imagem_livro, l.isbn_10_livro, l.isbn_13_livro, a.id_autor, a.nm_autor FROM livro l INNER JOIN autor a on a.id_autor = l.id_autor"
    sql = "select l.id_livro, l.isbn_10_livro, l.isbn_13_livro, il.id_info_livro, il.titulo_livro, c.id_capa, c.ds_capa, a.id_autor, a.nm_autor "
    sql = sql + "from livro l "
    sql = sql + "inner join info_livro il on il.id_info_livro = l.id_info_livro "
    sql = sql + "inner join capa c on c.id_capa = l.id_capa "
    sql = sql + "inner join autor a on a.id_autor = il.id_autor "
    sql = sql + "where c.ds_capa != 'eBook Kindle';"
    print(sql)
    cursor.execute(sql)
    resultado = cursor.fetchall()

    livros = []
    for registro in resultado:
        livro_info = {
        'id': registro[0],
        'isbn10': registro[1],
        'isbn13': registro[2],
        'idInfoLivro': registro[3],
        'titulo': registro[4],
        'idCapa': registro[5],
        'capa': registro[6],        
        'idAutor': registro[7],
        'autor': registro[8],
        }

        livros.append(livro_info)

    RasparLista(livros)        
        
            
scrapper()


        