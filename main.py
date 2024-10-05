from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from time import sleep
import json
from datetime import datetime, date
import gc
import platform
import subprocess
import os

class Main:
    def start(self):
        # os.system("taskkill /f /im chrome.exe")
        # os.system("pkill -f chrome")
        # if platform.system() == "Windows":
        #     subprocess.Popen(
        #         f'"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" --log-level=3 --remote-debugging-port=9222', shell=True)
        # if platform.system() == "Linux":
        #     subprocess.Popen(
        #         f'/usr/bin/google-chrome --log-level=3 --remote-debugging-port=9222', shell=True)
        service = Service()
        self.options = webdriver.ChromeOptions()
        # self.options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("disable-infobars")
        self.options.add_argument("--disable-extensions")
        self.options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(service=service ,options=self.options)
        self.driver.get('https://grilodasorte.bet')
        sleep(3)
    
    def carregar_dados(self):
        try:
            self.ultimos = []
            self.hora_atual = datetime.today().hour
            self.data_atual = date.today()
            with open('config.json', 'r') as config_file:
                self.config = json.load(config_file)
                config_file.close()
        except FileNotFoundError:
            exit()

    def logar(self):
        try:
            if(len(self.driver.find_elements(By.CSS_SELECTOR, '.content-logged a'))) == 0: return
            self.driver.find_elements(By.CSS_SELECTOR, '.content-logged a')[0].click()
            sleep(2)
            self.driver.find_elements(By.CSS_SELECTOR, 'input[type="email"]')[0].click()
            self.driver.find_elements(By.CSS_SELECTOR, 'input[type="email"]')[0].clear()
            self.driver.find_elements(By.CSS_SELECTOR, 'input[type="email"]')[0].send_keys(self.config['user'])
            sleep(2)
            self.driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')[0].click()
            self.driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')[0].clear()
            self.driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')[0].send_keys(self.config['password'])
            sleep(2)
            self.driver.find_elements(By.CSS_SELECTOR, 'input[type="password"]')[0].send_keys(Keys.ENTER)
            sleep(5)
        except: pass
        
    def entrar_no_jogo(self):
        self.driver.get('https://grilodasorte.bet/game/pragmatic-baccarat-1')
        sleep(5)
        url = self.driver.find_elements(By.CSS_SELECTOR, 'iframe')[0].get_attribute('src')
        self.driver.get(url)
        sleep(5)
        iframe = self.driver.find_elements(By.CSS_SELECTOR, 'iframe#game-iframe')[0]
        self.driver.switch_to.frame(iframe)
        sleep(5)
        try: self.driver.find_elements(By.CSS_SELECTOR, 'button[label="MAIS TARDE"]')[0].click()
        except: pass
        sleep(1)
        self.driver.find_elements(By.CSS_SELECTOR, '.NavRight_navRightMenuIconsContainer__foqok > div')[-1].click()

    
    def esperar_resultados_mudar(self):
        esperar = 0
        resultados = []
        while True:
            self.clique_para_evitar_inatividade()
            resultados = self.pegar_ultimos_resultados()
            sleep(1)
            if resultados != self.ultimos:
                break
            esperar+=1
            if(esperar) == 250: raise Exception('resultados não encontrados')
        return resultados
    
    def pegar_ultimos_resultados(self):
        resultados_tratados = []

        colunas = self.driver.find_elements(By.CSS_SELECTOR, '.bead-plate-container > div')
        for coluna in colunas:
            resultadosNaTela = coluna.find_elements(By.CSS_SELECTOR, '.entry-score')
            for resultadoNatela in resultadosNaTela:
                if "B" in resultadoNatela.text.upper():
                    resultados_tratados.append("Banker")
                elif "J" in resultadoNatela.text.upper():
                    resultados_tratados.append("Player")
                elif "E" in resultadoNatela.text.upper():
                    resultados_tratados.append("Tie")
        resultados_tratados.reverse()
        resultados_tratados = resultados_tratados[0:10]
        return resultados_tratados
    
    def bater_estrategia_alerta(self, sequencia):
        # Padrões
        if self.ultimos[0:3][::-1] == ["Banker", "Player", "Player"]: return True
        elif self.ultimos[0:3][::-1] == ["Player", "Banker", "Banker"]: return True
        elif self.ultimos[0:2][::-1] == ["Player", "Player"]: return True
        elif self.ultimos[0:2][::-1] == ["Banker", "Banker"]: return True
        # Repetição
        banker = 0
        player = 0
        for resultado in self.ultimos[0:(sequencia-1)]:
            if resultado == "Banker": banker+=1
            elif resultado == "Player": player+=1
        if banker == sequencia: return "Player"
        if player == sequencia: return "Banker"
        return

    def bater_estrategia(self, sequencia):
        # Padrões
        if self.ultimos[0:4][::-1] == ["Banker", "Player", "Player", "Player"]: return "Banker"
        elif self.ultimos[0:4][::-1] == ["Player", "Banker", "Banker", "Banker"]: return "Player"
        elif self.ultimos[0:3][::-1] == ["Player", "Player", "Tie"]: return "Banker"
        elif self.ultimos[0:3][::-1] == ["Banker", "Banker", "Tie"]: return "Player"
        # Repetição
        banker = 0
        player = 0
        for resultado in self.ultimos[0:sequencia]:
            if resultado == "Banker": banker+=1
            elif resultado == "Player": player+=1
        if banker == sequencia: return "Player"
        if player == sequencia: return "Banker"
        return

    def verificar_resultado(self, confirmacao):
        martingales = self.config['martingale']
        tentativas = 0
        while tentativas < martingales:
            self.ultimos = self.esperar_resultados_mudar()
            
            if self.ultimos[0] == confirmacao:
                return
            elif self.ultimos[0] == "Tie":
                self.apostar(tentativas, confirmacao)
            else:
                tentativas += 1
                self.apostar(tentativas, confirmacao)

    def reset(self):
        try:
            self.driver.quit()
            del self.driver
            gc.collect()
        except: pass
    
    def clique_para_evitar_inatividade(self):
        try:
            self.driver.find_elements(By.CSS_SELECTOR, 'button[label="Ok"]')[0].click()
        except: pass
    
    def recarregar_pagina(self):
        self.driver.refresh()
        sleep(2)
        iframe = self.driver.find_elements(By.CSS_SELECTOR, 'iframe')[0]
        self.driver.switch_to.frame(iframe)        
        try: self.driver.find_elements(By.CSS_SELECTOR, 'button[label="MAIS TARDE"]')[0].click()
        except: pass
        sleep(1)
        self.driver.find_elements(By.CSS_SELECTOR, '.NavRight_navRightMenuIconsContainer__foqok > div')[-1].click()
        sleep(1)
    
    def apostar(self, multiplicador, confirmacao):
        self.driver.find_elements(By.CSS_SELECTOR, 'div[color="#8694C4"]')[0].click()
        sleep(0.1)
        elemento = "Player" in confirmacao if 0 else 1
        self.driver.find_elements(By.CSS_SELECTOR, f'div[data-betcode="{elemento}"] > div')[0].click()
        sleep(0.1)
        for g in range(multiplicador):
            self.driver.find_elements(By.CSS_SELECTOR, '.Tooltip-Wrapper')[9].click()
        sleep(0.1)
            
    def main(self):
        self.carregar_dados()
        while True:
            try:
                self.temporizador = 0
                self.start()
                self.logar()
                self.entrar_no_jogo()
                while True:
                    self.clique_para_evitar_inatividade()
                    self.ultimos = self.esperar_resultados_mudar()
                    confirmacao = self.bater_estrategia(self.config['sequencia'])
                    if confirmacao:
                        self.apostar(0, confirmacao)
                        self.verificar_resultado(confirmacao)
                    self.temporizador+=1
                    if self.temporizador % 5 == 0:
                        self.recarregar_pagina()
                    if self.temporizador >= 30 : raise Exception("Reiniciando o bot!")
                    sleep(10)
            except Exception as error: 
                print(error)
                self.reset()

if __name__ == '__main__':
    main = Main()
    main.main()