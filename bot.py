import os
import time
import json
import requests

class User:
    # veja https://core.telegram.org/bots/api#user
    # para saber quais serão os possíveis atributos dos objetos User()
    def __init__(self, **field):
        self.__dict__.update(field)
    def getAttribsList(self):
        return list(self.__dict__.keys())

class Message:
    # veja https://core.telegram.org/bots/api#message
    # para saber quais serão os possíveis atributos dos objetos Message()
    def __init__(self, **field):
        if "from" in field.keys():          # "from" é uma palavra resevada do python, não podemos usar como atributo
            field["m_from"] = field["from"] # m_from -> message_from
            del field["from"]
        self.__dict__.update(field)
    def getAttribsList(self):
        return list(self.__dict__.keys())

class ExtractData:
    def __init__(self):
        self.datas = {}             # Todas as mensagens recebidas serão armazenadas aqui.
        
        # Diferência as mensagens enviadas para o Bot com o update_id das atualizações
        # Eles serão iguais enquanto o usuário não enviar uma nova mensagem
        self.current_update_id = 0  # Armazenada o update_id da mensagem atual.
        self.previous_update_id = -1 # Armazenada o update_id da mensagem anterior (current_update_id - 1).

        # Verifica quando foi enviada a primeira msg depois
        # da execução do script, no formato unix.
        # (https://core.telegram.org/bots/api#message; field date)
        self.check_time = 0         
        self.datetime_msg = None
        self.datetime_init = None

    def getInitialTime(self, message):
        if self.check_time == 1:
            # Agora podemos saber o update_id da primeira msg enviada (self.current_update_id).
            return

        self.datetime_msg = message.date

        if message.date >= self.datetime_init:
            self.datetime_msg = message.date
            self.check_time = 1

        return

    def getUser(self, update):
        return User(**update["message"]["from"])

    def getMessage(self, update):
        return Message(**update["message"])

    def getCurrentUpdate(self, update_result):
        update = update_result[-1]
        self.previous_update_id = self.current_update_id
        self.current_update_id = update["update_id"]
        return update

    def getData(self, update_result, lastMsg=False):
        update = self.getCurrentUpdate(update_result)
        if self.previous_update_id != self.current_update_id:
            _message_obj = self.getMessage(update)
            _message_obj.m_from = self.getUser(update)
            self.getInitialTime(_message_obj)
            data = {self.current_update_id: _message_obj}
            del _message_obj

            if lastMsg:
                self.datas = {}     # Guardará somente a última mensagem enviada ao Bot

            self.datas.update(data)
        return

class TelegramBot:
    def __init__(self, token):
        token = token
        self.url_base = f'https://api.telegram.org/bot{token}/'

        # Marca o tempo do inico da execução do script, no formato Unix (em segundos)
        self.utc_datetime = None

        self.extract_data = ExtractData()

        # Inicia a opção da Aposta
        # já que ela vai ser solicitada devemos iniciar ela.
        self.opcao = 0 

    def Iniciar(self):
        self.utc_datetime = int(time.time()) # start
        self.extract_data.datetime_init = self.utc_datetime
        
        running_bot = True
        try:
            while running_bot:
                update = self.getMessages()
                dados = update["result"]

                if not dados:
                    continue

                self.extract_data.getData(dados, lastMsg=True)
                if self.extract_data.datetime_msg < self.utc_datetime:
                    # Faça algo somente com as mensagens enviadas após a execução script
                    # (ou se quiser, faça algo com a última mensagem encontrada).
                    continue

                self.apostaPerguntas()
                
        except KeyboardInterrupt:
            exit("Good bye.")
        finally:
            running_bot = False

    def apostaPerguntas(self):
        mensagem = self.extract_data.datas[self.extract_data.current_update_id] # Obtem o obj Message() do update_id atual
        if "text" not in mensagem.getAttribsList(): # Verifica se a mensagem tem o atributo text
            return 
        if mensagem.text == '1':
            self.opcao = mensagem.message_id
            self.responder(f'''Digite o sinal para aposta única no seguinte formato: (exemplo) EURUSD|15:00|M5|PUT|20{os.linesep}Ou seja: ATIVO|HORA|MINUTAGEM|PUT OU CALL|VALOR''', mensagem.m_from.id)
        
        if mensagem.text == '2':
            self.opcao = mensagem.message_id
            self.responder(f'''Carregue sua lista formatada''', mensagem.m_from.id)
        
        # Você quer verificar se a mensagem enviada pelo o usuário é a resposta
        # para a opção selecionada, então verifiquemos se o id da nova mensagem
        # (message_id) enviada pelo usuário bate com a sequência. Já que message_id
        # é o id da mensagem anterior mais 2.
        if mensagem.message_id == self.opcao + 2:
            self.opcao = 0  # Reset para não ficar imprimindo na tela o tempo todo, para caso que o usuário não envie mais nada
            apostaResposta = mensagem.text
            transacao = f"""DADOS DO NEGOCIANTE\nID:\t\t{mensagem.m_from.id}\nPRIMEIRO NOME:\t{mensagem.m_from.first_name}\nORDEM:\t\t{apostaResposta}\n"""
            print(transacao)

    def getMessages(self):
      ##link da api pra obter novas atualizações
        link_requisicao = f'{self.url_base}getUpdates?timeout=100'
        ##se tiver algo novo
        resultado = requests.get(link_requisicao)
        return json.loads(resultado.content)

    # Responder
    def responder(self, resposta, chat_id):
        if self.extract_data.previous_update_id != self.extract_data.current_update_id:      # Sem isso vai continuar mandando mensagens para o usuário, spam
            link_requisicao = f'{self.url_base}sendMessage?chat_id={chat_id}&text={resposta}'
            requests.get(link_requisicao)


if __name__ == "__main__":
    token = ""
    bot = TelegramBot(token)
    bot.Iniciar()
