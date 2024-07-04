import pandas as pd
import requests
import re
import unidecode
from docx import Document
import os

ARTISTAS = set(["Abdias Nascimento", "Arissana Pataxó", "Asurini do Alto Xingu"])    # Artistas disponíveis
planilha = None     # Dataframe da planilha de dados auxiliar do projeto

# Classe que modela um artista e todas as informações disponíveis para uso no CKAN ou como metadado para a extensão DCAT

class Artista:

    def __init__(self):
        self.nome = ""
        self.sobrenome = ""
        self.nome_completo = ""
        self.imagens = {}
        self.descricao = ""
        self.links = []
        self.atualizacao = ""
        self.genero = ""
        self.pesquisante = ""
        self.email_pesquisante = ""
        self.data_nascimento = ""
        self.palavras_chave = []
        self.pagina = ""

    def imprime_artista(self):
        print(self.nome_completo)
        print(self.imagens)
        print(self.descricao)
        print(self.links)
        print(self.atualizacao)
        print(self.genero)
        print(self.pesquisante)
        print(self.email_pesquisante)
        print(self.data_nascimento)
        print(self.palavras_chave)
        print(self.pagina)

    # Coleta as imagens e suas informações a partir do documento do artista em questão

    '''
        O padrão dos documentos é:

            - Nome do artista
            - Lista de imagens
                - Nome da foto
                - Propriedades (existentes ou não, de 2 a 4 linhas, com exceção de 5 em um caso)
                - Descrição
                - Fonte
            - Trajetória
            - Produção
            - Links
            - Última atualização
    '''

    def _captura_imagens(self, paragrafos, indice, dados_obra, paragrafo):

        self.imagens[paragrafo] = {}
        ultima_foto = paragrafo
        indice += 1
        paragrafo = paragrafos[indice]

        # Para o caso de foto sem propriedades

        while not paragrafo.startswith("Descrição") and not paragrafo.startswith("Audiodescrição"):
            
            dados_obra.append(paragrafos[indice])      
            indice += 1
            paragrafo = paragrafos[indice]

        # Obtém a descrição

        if paragrafos[indice].startswith("Descrição"):
            
            descricao = paragrafos[indice].split("Descrição: ")[1]

            self.imagens[ultima_foto]["descricao"] = descricao

            indice += 1

        elif paragrafos[indice].startswith("Audiodescrição"):

            descricao = paragrafos[indice].split("Audiodescrição: ")[1]
            self.imagens[ultima_foto]["descricao"] = descricao

            indice += 1

        # Se não tem título, ele deve ser o próprio nome do arquivo. Caso contrário, obtém o apresentado

        if len(dados_obra) and not dados_obra[0].startswith("s/") and not dados_obra[0].startswith("S/"):

            self.imagens[ultima_foto]["titulo"] = dados_obra[0]

        # Fotos com 3 ou 4 propriedades podem ter área da pintura, comprimento da obra e ano de obra na terceira linha

        if len(dados_obra) in (3, 4):
            self.imagens[ultima_foto]["descricao"] += ("\n<br>\n" + dados_obra[1].capitalize().strip()) \
                        if self.imagens[ultima_foto]["descricao"] != "" else dados_obra[1].capitalize().strip()
            
            eArea = re.compile("[0-9\,]{1,5} *[xX] *[0-9\,]{1,5} *(cm)?")
            eAno = re.compile("[0-9]{4}")
            eComprimento = re.compile("[0-9]{1,3}(?= *cm)")

            if eArea.match(dados_obra[2]):
                self.imagens[ultima_foto]["area"] = dados_obra[2]

            elif eAno.search(dados_obra[2]):
                achado = eAno.search(dados_obra[2])
                self.imagens[ultima_foto]["ano"] = achado.group(0)

            elif eComprimento.search(dados_obra[2]):
                achado = eComprimento.search(dados_obra[2])
                self.imagens[ultima_foto]["comprimento"] = float(achado.group(0)) / 100.0

        # Análogo ao anterior, mas somente ano na quarta linha

        if len(dados_obra) == 4:
            eAno = re.compile("[0-9]{4}")
            achado = eAno.search(dados_obra[3])
            if achado:
                self.imagens[ultima_foto]["ano"] = achado.group(0)

        # Análogo ao anterior

        if len(dados_obra) == 2:
            eAno = re.compile("[0-9]{4}")
            achado = eAno.search(dados_obra[1])
            if achado:
                self.imagens[ultima_foto]["ano"] = achado.group(0)

        # Todas as propriedades lidas, lê a fonte da foto

        if paragrafos[indice].startswith("Fonte:"):
            self.imagens[ultima_foto]["fonte"] = paragrafos[indice].split("Fonte:")[1].strip()
            indice += 1

        return indice
    
    # Lê os dados do artista: trajétoria, produção e links. Por fim, lê a data da atualização. Segue o mesmo padrão de leitura das imagens
    
    def _captura_detalhes_artista(self, paragrafos, indice, paragrafo):

        indice += 1
        paragrafo = paragrafos[indice]

        self.descricao += "**Trajetória**\n<br>\n" + paragrafo

        indice += 1
        paragrafo = paragrafos[indice]            

        while not paragrafo.startswith("Produção"):

            self.descricao += f" {paragrafo}"

            indice += 1
            paragrafo = paragrafos[indice]

        indice += 1

        self.descricao += "\n<br>\n**Produção**\n<br>\n" + paragrafos[indice]

        indice += 1
        paragrafo = paragrafos[indice]  

        while not paragrafo.startswith("Links"):
            self.descricao += f" {paragrafo}"

            indice += 1
            paragrafo = paragrafos[indice]

        indice += 1
        paragrafo = paragrafos[indice]

        while not paragrafo.startswith("Última atualização"):
            
            if paragrafo.startswith("http"):    # Ignora os nomes dos links
                self.links.append(paragrafo)

            indice += 1
            paragrafo = paragrafos[indice]

        indice += 1
        paragrafo = paragrafos[indice]

        self.atualizacao = paragrafo

        return indice
    
    # Filtra a planilha para obter somentes os artistas disponíveis
    
    def _obtem_informacao_artista_planilha(self):

        dados = planilha.query(f'Item == "{self.nome_completo}"')
        
        self.pesquisante = dados["Pesquisante"].values[0]
        self.email_pesquisante = dados["E-mail Pesquisante"].values[0]
        self.data_nascimento = dados["Data inicio/nasc"].values[0]
        self.palavras_chave = [tag.replace(",", "") for tag in dados["Palavras-chave"].values[0].split(" ") if tag]
        self.genero = dados["Gênero"].values[0]
        self.pagina = dados["Link p/ site"].values[0]

    # Carrega os dados e imagens de todos os artistas

    def inicializa_artista(self, artista : str):
    
        documento = Document(f"{artista}/RV_{artista}.docx")
        paragrafos = [x.text for x in documento.paragraphs if x.text]   # Tira linhas em branco
        nome = self.nome_completo = paragrafos[0]

        if len(nome.split(" ")) == 2:
            self.nome, self.sobrenome = nome.split(" ")
        else:
            self.nome, self.sobrenome = nome.split(" ")[0], " ".join(nome.split()[1:])

        padrao_foto = re.compile("[a-zA-Z][a-zA-Z]_|.*\.(jpg|jpeg|png)")
        indice = 1

        while indice != len(paragrafos) - 1:

            paragrafo = paragrafos[indice]
            dados_obra = []

            if padrao_foto.match(paragrafo):

                indice = self._captura_imagens(paragrafos, indice, dados_obra, paragrafo)

            elif paragrafo.startswith("Trajetória"):

                indice = self._captura_detalhes_artista(paragrafos, indice, paragrafo)

            else:
                indice += 1

        self._obtem_informacao_artista_planilha()

# Classe que disponibiliza criação de organização, dataset e recursos de acordo com a API do CKAN

class Requisicoes:
    
    def __init__(self, token : str):
        self.header = {"Authorization" : token}
        self.ckan_url = 'http://10.0.2.15:5000/api/3/action/'

    def cria_organizacao(self, params : dict):

        url = self.ckan_url + 'organization_create'

        params['name'] = unidecode.unidecode(params.get("name").lower().replace(" ", "_"))

        resposta = requests.post(url, headers = self.header, json = params)

        if resposta.json()['success'] == True:
            imprime_verde(f"Organização {params['name']} criada com sucesso. \n")
        else:
            imprime_vermelho(f"Erro ao criar a organização {params.get('name')}")
            imprime_vermelho(resposta.json())

        return resposta.json()
    
    def cria_dataset(self, params : dict):

        url = self.ckan_url + 'package_create'

        params['name'] = unidecode.unidecode(params.get("name").lower().replace(" ", "_"))

        resposta = requests.post(url, headers = self.header, json = params)

        if resposta.json()['success'] == True:
            imprime_verde(f"Dataset {params['name']} criado com sucesso. \n")
        else:
            imprime_vermelho(f"Erro ao criar o dataset {params.get('name')}")
            imprime_vermelho(resposta.json())

        return resposta.json()
    
    def cria_recurso(self, params : dict, arquivo):

        url = self.ckan_url + 'resource_create'

        # Cada recurso tem uma foto, enviada através de form-data de acordo com a documentação

        resposta = requests.post(url, headers = self.header, data = params, files = arquivo)

        if resposta.json()['success'] == True:
            imprime_verde(f"Recurso {params['name']} criado com sucesso. \n")
        else:
            imprime_vermelho(f"Erro ao criar recurso {params['name']}")
            imprime_vermelho(resposta.json())

        return resposta.json()
    

def imprime_vermelho(string): print("\033[91m{}\033[00m".format(string))
 
def imprime_verde(string): print("\033[92m{}\033[00m".format(string))

def ler_planilha():
    global planilha

    planilha = pd.read_csv('dados-artistas-projeto.tsv', sep='\t').query('Item in @ARTISTAS') # Obtém apenas os artistas que recebemos para trabalhar

def carregar_artista(nome_artista):

    artista = Artista()

    artista.inicializa_artista(nome_artista)

    return artista

def cria_dataset_artista(artista : Artista, id_organizacao, nome_grupo, requisicoes : Requisicoes):

    extras = [
        {"key" : "first_name", "value" : artista.nome},
        {"key" : "last_name", "value" : artista.sobrenome},
        {"key" : "gender" , "value" : artista.genero},
        {"key" : "birthday" , "value" : artista.data_nascimento},
        {"key" : "homepage" , "value" : artista.pagina},
        {"key" : "modified" , "value" : artista.atualizacao},
        {"key" : "links" , "value" : ",".join([link for link in artista.links])}
    ]

    params = {
        "name"  : f"{artista.nome.lower()}_{artista.sobrenome.lower().replace(' ', '')}",
        "title" : f"{artista.nome} {artista.sobrenome}",
        "maintainer" : artista.pesquisante,
        "maintainer_email" : artista.email_pesquisante,
        "notes" : artista.descricao,
        "tags" : [{"name" : nome} for nome in artista.palavras_chave],
        "groups" : [{"name" : nome_grupo}],
        "owner_org" : id_organizacao,
        "extras" : extras
    }

    return requisicoes.cria_dataset(params)

def cria_recurso_dataset(id_dataset, artista : Artista, imagem : str, requisicoes : Requisicoes):

    params_recurso = {
        "package_id" : id_dataset
    }

    params_recurso['description'] = artista.imagens[imagem]['descricao']

    if artista.imagens[imagem].get('area') != None:

        params_recurso['hasArea'] = artista.imagens[imagem].get('area')

    elif artista.imagens[imagem].get('comprimento') != None:

        params_recurso['hasMetricLength'] = artista.imagens[imagem].get('comprimento')

    if artista.imagens[imagem].get('ano') != None:

        params_recurso['issued'] = artista.imagens[imagem].get('ano')

    if artista.imagens[imagem].get('fonte') != None:

        params_recurso['documentation'] = artista.imagens[imagem].get('fonte')

    if artista.imagens[imagem].get('titulo') != None:

        params_recurso['name'] = artista.imagens[imagem].get('titulo')
    
    else:

        params_recurso['name'] = imagem

    arquivo = {
        'upload': (f"{artista.nome_completo}/{imagem}", open(f"{artista.nome_completo}/{imagem}", "rb"))
    }
    
    return requisicoes.cria_recurso(params_recurso, arquivo)

def popula_ckan():

    requisicoes = Requisicoes('eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJtZ0RybWZsS2hob3ItSW9ieDFRNVNidk5JQ3kxUFhBT2ho'
                            'ZlVyZU1DekZYZU43c01MRlhQeExpRVY2RG5fTW52TWc0RE1MeW1jVkEzWm15N1Uxc1dMV3RlSXZoeVItQWttc3FfaFl3ZWx'
                            'QRG9SSVdnR2NFc1BjUENVOG9CTEJOUGE3Smc4c05sY2FuaDZPTEkxS3NaOUdTYlhkVVEyM0lwQlEtOURZeE1RTGlpTVN2OV'
                            'BkaTdteEFlcks0cUdhYU96RVlQVWJYQXRFSzVzWHlqLUc0ZDFtMUVnUm81OVp4NGNlZlRwMnMxSDk0RHZZSlZIRHd6ZGxJS'
                            'DRtNy1qOWlWRFdiRGJiMXltR1VMNWQ4NUpxYkJiVGVIRjBxVnBBTFQzNHpLU29lNHpBWU00TThVSDBUZ200ZFVVNmhfX1hUN'
                            'UpOUTdHYW54LWEtX1J0Sm5KTHhUd3ciLCJpYXQiOjE3MTc5NzU2MzR9.vXQNWyrZ3nagBbasOkRXcgQFkn46M_phHeao49MdZBk')
    
    resposta = requisicoes.cria_organizacao({"title" : "CAp UFRJ",
                                            "name" : "CAp UFRJ",
                                            "extras" : [{}],
                                            "packages" : [{}],
                                            "users" : [{"name" : "maya_inbar"}]})
    
    if resposta['success']:
        id_organizacao = resposta['result']['id']

    else:
        return
    
    for pasta in os.listdir():

        if pasta in ARTISTAS:

            artista = carregar_artista(pasta)

            resposta = cria_dataset_artista(artista, id_organizacao, "cap_ufrj", requisicoes)

            id_dataset = resposta['result']['id']

            for imagem in artista.imagens:

                cria_recurso_dataset(id_dataset, artista, imagem, requisicoes)
    
    
def main():

    ler_planilha()

    popula_ckan()

if __name__ == "__main__":
    main()
