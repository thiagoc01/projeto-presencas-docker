# Projeto Final Governança e Gestão de Dados 2024.1 - Projeto Presenças - CAp UFRJ

Este repositório contém a implementação de um repositório CKAN com as obras de três artistas do Projeto Presenças do CAp UFRJ. A stack de Docker está previamente configurada e com as obras hospedadas com seus respectivos metadados configurados.
As extensões utilizadas estão exibidas no arquivo .env da stack.

### Diretório projeto
---

Contém as pastas dos três artistas fornecidos a nós com suas obras e arquivos descritivos delas e dos artistas. O arquivo `automatizador.py` é um script em Python que carrega no CKAN todos os artistas nesse diretório. Ele foi pensado e adaptado para os .docx presentes. O arquivo `dados-artistas-projeto.tsv` apresenta informações adicionais de cada artista do projeto. Ele também é utilizado pelo script para adição de metadados. Para utilizar o automatizador, basta deletar todos os datasets e a organização no CKAN e executar o script.

**:warning: Lembre-se de alterar o IP na URL do script. Também lembre-se de deletar da lixeira do CKAN os datasets e a organização, caso contrário haverá erro.**

### Diretório ckan-docker
---

Contém a stack em Docker capaz de subir o CKAN. As pastas têm os seguintes conteúdos:


| Diretório | Conteúdo |
|--|--|
| persistencia | Contém os volumes dos dados de cada serviço utilizado no CKAN |
| postgresql | Ingredientes para o build da imagem ao subir o serviço via Compose |
| ckan | Ingredientes para o build da imagem do CKAN. Importante citar que a construção deve ser feita pelo usuário via `docker build` |
| datapusher-plus | Ingredientes para o build da imagem do datapusher-plus


## Instruções para deploy:

1. Clone este repositório e acesse o diretório `ckan-docker`;
2. Crie a rede dos containers:
    ```bash
    $ sudo docker network create ckan-marilu
    ```
3. Acesse o diretório `ckan` e rode:
    ```bash
    $ sudo docker build -t ckan:2.10.1 . && cd ..
    ```
4. Modifique o arquivo `.env` alterando 10.0.2.15 para o IP de sua máquina. (Se você está numa VM no VirtualBox em NAT não é necessário alterar);
5. Acesse o diretório `persistencia` e rode:
    ``` bash
    $ mkdir banco_dados && tar -xzf base.tar.gz -C banco_dados/
    $ sudo chown 70 -R banco_dados/
    $ sudo chown 92:92 -R dados/
    $ sudo chown 8983:8983 -R solr/
    $ sudo chmod 700 banco_dados/
    $ sudo chmod 755 dados/
    $ sudo chmod 755 solr/
    $ cd ..
    ```
6. Coloque a stack no ar com:
    ```bash
    $ sudo docker compose up -d
    ```

:warning: Certifique-se que a porta 5000 esteja disponível

:wastebasket: Você pode apagar o arquivo base.tar.gz se quiser

## Como utilizar?

Certifique-se que a stack subiu com sucesso ao rodar
```bash
$ sudo docker compose ps
```
e todos estarem up.

Após isso, acesse a URL no IP que você editou o `.env` na porta 5000 (ex.: `http://10.0.2.15:5000`).

Vá na guia de login e acesse com a conta de administrador presente no arquivo `.env`. A conta criada por nós é da coordenadora do projeto, Maya Inbar.

Caso você queira testar o script criado por nós, delete todos os datasets e organizações.

:warning: Como o IP será alterado, é possível que ocorra erros com as URLs dos recursos após clonar o CKAN e subi-lo.