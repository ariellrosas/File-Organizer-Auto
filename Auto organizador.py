import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import shutil
import time
import threading
from pathlib import Path
import sys
import pystray
from PIL import Image, ImageDraw
import logging
from queue import Queue, Empty

class OrganizadorArquivos:
    def __init__(self, root):
        self.root = root
        self.root.title("Organizador de Arquivos Auto v2")
        self.root.geometry("850x650")
        self.root.protocol('WM_DELETE_WINDOW', self.minimizar_para_bandeja)
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('organizador.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger()
        
        # Locks para operações thread-safe
        self.regras_lock = threading.Lock()
        self.arquivo_lock = threading.Lock()
        
        # Configurações
        self.arquivo_config = "config.json"
        self.regras = []
        self.monitorando = True
        self.pausado = False
        self.editando_index = None
        
        # Queue para comunicação thread-safe entre threads
        self.log_queue = Queue()
        
        # Criar interface
        self.criar_interface()
        
        # Carregar regras salvas
        self.carregar_regras()
        
        # Iniciar bandeja do sistema
        self.iniciar_bandeja_sistema()
        
        # Iniciar monitoramento
        self.iniciar_monitoramento()
        
        # Iniciar processamento da queue de log
        self.processar_log_queue()
        
    def criar_interface(self):
        """Cria a interface gráfica do aplicativo"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Título
        titulo = ttk.Label(main_frame, text="Organizador de Arquivos Auto v2", 
                          font=('Arial', 16, 'bold'))
        titulo.grid(row=0, column=0, columnspan=4, pady=(0, 20))
        
        # Frame de adição de regras
        frame_regra = ttk.LabelFrame(main_frame, text="Nova Regra / Editar Regra", padding="10")
        frame_regra.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(0, 10))
        frame_regra.columnconfigure(1, weight=1)
        
        # Pasta monitorada
        ttk.Label(frame_regra, text="Pasta Monitorada:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.entry_monitorar = ttk.Entry(frame_regra, width=50)
        self.entry_monitorar.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        ttk.Button(frame_regra, text="Procurar", 
                  command=self.procurar_pasta_monitorar).grid(row=0, column=2, padx=(5, 0))
        
        # Extensões
        ttk.Label(frame_regra, text="Extensões (ex: .txt, .pdf, .pasta, .tudo):").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.entry_extensoes = ttk.Entry(frame_regra, width=50)
        self.entry_extensoes.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        
        # Campo "Exceção"
        ttk.Label(frame_regra, text="Exceção:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.entry_excecoes = ttk.Entry(frame_regra, width=50)
        self.entry_excecoes.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        ttk.Label(frame_regra, text="ex: .exe, .tmp, .pasta_selecionadas, .extensao_selecionadas").grid(row=2, column=2, sticky=tk.W, padx=(5, 0))
        
        # Pasta destino
        ttk.Label(frame_regra, text="Pasta Destino:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.entry_destino = ttk.Entry(frame_regra, width=50)
        self.entry_destino.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2, padx=(5, 0))
        ttk.Button(frame_regra, text="Procurar", 
                  command=self.procurar_pasta_destino).grid(row=3, column=2, padx=(5, 0))
        
        # Botões adicionar/editar
        frame_botoes_regra = ttk.Frame(frame_regra)
        frame_botoes_regra.grid(row=4, column=0, columnspan=3, pady=10)
        
        self.btn_adicionar = ttk.Button(frame_botoes_regra, text="Adicionar Regra", 
                                       command=self.adicionar_regra)
        self.btn_adicionar.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_editar = ttk.Button(frame_botoes_regra, text="Salvar Edição", 
                                    command=self.salvar_edicao, state=tk.DISABLED)
        self.btn_editar.pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(frame_botoes_regra, text="Cancelar Edição", 
                  command=self.cancelar_edicao).pack(side=tk.LEFT)
        
        # Lista de regras
        frame_lista = ttk.LabelFrame(main_frame, text="Regras Ativas", padding="10")
        frame_lista.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        frame_lista.columnconfigure(0, weight=1)
        frame_lista.rowconfigure(0, weight=1)
        
        # Treeview para regras
        colunas = ('monitorar', 'extensoes', 'excecoes', 'destino')
        self.tree_regras = ttk.Treeview(frame_lista, columns=colunas, show='headings', height=8)
        
        # Definir cabeçalhos
        self.tree_regras.heading('monitorar', text='Pasta Monitorada')
        self.tree_regras.heading('extensoes', text='Extensões')
        self.tree_regras.heading('excecoes', text='Exceções')
        self.tree_regras.heading('destino', text='Pasta Destino')
        
        # Configurar colunas
        self.tree_regras.column('monitorar', width=200)
        self.tree_regras.column('extensoes', width=150)
        self.tree_regras.column('excecoes', width=150)
        self.tree_regras.column('destino', width=200)
        
        self.tree_regras.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar para treeview
        scrollbar = ttk.Scrollbar(frame_lista, orient=tk.VERTICAL, command=self.tree_regras.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree_regras.configure(yscrollcommand=scrollbar.set)
        
        # Frame botões regras
        frame_botoes_regras = ttk.Frame(frame_lista)
        frame_botoes_regras.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(frame_botoes_regras, text="Editar Regra Selecionada", 
                  command=self.editar_regra).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(frame_botoes_regras, text="Remover Regra Selecionada", 
                  command=self.remover_regra).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(frame_botoes_regras, text="Limpar Todas as Regras", 
                  command=self.limpar_regras).pack(side=tk.LEFT)
        
        # Área de log
        frame_log = ttk.LabelFrame(main_frame, text="Log de Atividades", padding="10")
        frame_log.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E, tk.N, tk.S))
        frame_log.columnconfigure(0, weight=1)
        frame_log.rowconfigure(0, weight=1)
        
        self.text_log = tk.Text(frame_log, height=8, wrap=tk.WORD)
        self.text_log.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar_log = ttk.Scrollbar(frame_log, orient=tk.VERTICAL, command=self.text_log.yview)
        scrollbar_log.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.text_log.configure(yscrollcommand=scrollbar_log.set)
        
        # Frame status
        frame_status = ttk.Frame(main_frame)
        frame_status.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_var = tk.StringVar(value="Status: Monitoramento ATIVO")
        ttk.Label(frame_status, textvariable=self.status_var).pack(side=tk.LEFT)
        
        # Botão pausar/retomar
        self.btn_pausar = ttk.Button(frame_status, text="Pausar Monitoramento", 
                                    command=self.alternar_pausa)
        self.btn_pausar.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Configurar weights para expansão
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(3, weight=1)
    
    def validar_path(self, caminho, deve_existir=True):
        """Valida se um caminho é válido e seguro"""
        try:
            path = Path(caminho)
            if deve_existir and not path.exists():
                return False, f"O caminho não existe: {caminho}"
            
            # Verificar se é um caminho absoluto
            if not path.is_absolute():
                return False, "O caminho deve ser absoluto"
                
            return True, "OK"
        except Exception as e:
            return False, f"Erro ao validar caminho: {str(e)}"
    
    def validar_extensoes(self, extensoes_str):
        """Valida a lista de extensões, incluindo as regras especiais"""
        extensoes = [ext.strip().lower() for ext in extensoes_str.split(',') if ext.strip()]
        
        if not extensoes:
            return False, "Digite pelo menos uma extensão"
        
        for ext in extensoes:
            # Permitir as regras especiais
            if ext in ['.pasta_selecionadas', '.extensao_selecionadas']:
                continue
            if not ext.startswith('.'):
                return False, f"Extensão deve começar com ponto: {ext}"
            if len(ext) < 2:
                return False, f"Extensão muito curta: {ext}"
            if any(c in ext for c in ' *?<>|"'):
                return False, f"Extensão contém caracteres inválidos: {ext}"
                
        return True, extensoes
    
    def procurar_pasta_monitorar(self):
        """Abre diálogo para selecionar pasta monitorada"""
        from tkinter import filedialog
        pasta = filedialog.askdirectory()
        if pasta:
            self.entry_monitorar.delete(0, tk.END)
            self.entry_monitorar.insert(0, pasta)
    
    def procurar_pasta_destino(self):
        """Abre diálogo para selecionar pasta destino"""
        from tkinter import filedialog
        pasta = filedialog.askdirectory()
        if pasta:
            self.entry_destino.delete(0, tk.END)
            self.entry_destino.insert(0, pasta)
    
    def adicionar_regra(self):
        """Adiciona uma nova regra à lista com validação"""
        monitorar = self.entry_monitorar.get().strip()
        extensoes = self.entry_extensoes.get().strip()
        excecoes = self.entry_excecoes.get().strip()
        destino = self.entry_destino.get().strip()
        
        # Validação robusta
        if not all([monitorar, extensoes, destino]):
            messagebox.showerror("Erro", "Preencha todos os campos obrigatórios!")
            return
        
        # Validar paths
        valido, mensagem = self.validar_path(monitorar, deve_existir=True)
        if not valido:
            messagebox.showerror("Erro", f"Pasta monitorada inválida:\n{mensagem}")
            return
            
        valido, mensagem = self.validar_path(destino, deve_existir=False)
        if not valido:
            messagebox.showerror("Erro", f"Pasta destino inválida:\n{mensagem}")
            return
        
        # Validar extensões
        valido, resultado = self.validar_extensoes(extensoes)
        if not valido:
            messagebox.showerror("Erro", resultado)
            return
        extensoes_lista = resultado
        
        # Validar exceções
        valido, resultado = self.validar_extensoes(excecoes) if excecoes else (True, [])
        if not valido:
            messagebox.showerror("Erro", f"Exceções inválidas:\n{resultado}")
            return
        excecoes_lista = resultado if excecoes else []
        
        # Criar pasta destino se não existir
        if not os.path.exists(destino):
            try:
                os.makedirs(destino)
            except Exception as e:
                messagebox.showerror("Erro", f"Não foi possível criar pasta destino:\n{str(e)}")
                return
        
        nova_regra = {
            'monitorar': monitorar,
            'extensoes': extensoes_lista,
            'excecoes': excecoes_lista,
            'destino': destino
        }
        
        # Operação thread-safe
        with self.regras_lock:
            self.regras.append(nova_regra)
            self.salvar_regras()
        
        self.atualizar_lista_regras()
        self.limpar_campos_regra()
    
    def editar_regra(self):
        """Prepara a interface para editar uma regra existente"""
        selecionado = self.tree_regras.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione uma regra para editar!")
            return
        
        self.editando_index = int(selecionado[0].lstrip('I'))
        
        # Operação thread-safe
        with self.regras_lock:
            if 0 <= self.editando_index < len(self.regras):
                regra = self.regras[self.editando_index]
                
                # Preencher campos com dados da regra
                self.entry_monitorar.delete(0, tk.END)
                self.entry_monitorar.insert(0, regra['monitorar'])
                
                self.entry_extensoes.delete(0, tk.END)
                self.entry_extensoes.insert(0, ', '.join(regra['extensoes']))
                
                self.entry_excecoes.delete(0, tk.END)
                self.entry_excecoes.insert(0, ', '.join(regra['excecoes']))
                
                self.entry_destino.delete(0, tk.END)
                self.entry_destino.insert(0, regra['destino'])
                
                # Alterar estado dos botões
                self.btn_adicionar.config(state=tk.DISABLED)
                self.btn_editar.config(state=tk.NORMAL)
    
    def salvar_edicao(self):
        """Salva as alterações na regra sendo editada"""
        if self.editando_index is None:
            return
        
        monitorar = self.entry_monitorar.get().strip()
        extensoes = self.entry_extensoes.get().strip()
        excecoes = self.entry_excecoes.get().strip()
        destino = self.entry_destino.get().strip()
        
        if not all([monitorar, extensoes, destino]):
            messagebox.showerror("Erro", "Preencha todos os campos obrigatórios!")
            return
        
        # Validar extensões
        valido, resultado = self.validar_extensoes(extensoes)
        if not valido:
            messagebox.showerror("Erro", resultado)
            return
        extensoes_lista = resultado
        
        valido, resultado = self.validar_extensoes(excecoes) if excecoes else (True, [])
        if not valido:
            messagebox.showerror("Erro", f"Exceções inválidas:\n{resultado}")
            return
        excecoes_lista = resultado if excecoes else []
        
        # Operação thread-safe
        with self.regras_lock:
            if 0 <= self.editando_index < len(self.regras):
                self.regras[self.editando_index] = {
                    'monitorar': monitorar,
                    'extensoes': extensoes_lista,
                    'excecoes': excecoes_lista,
                    'destino': destino
                }
                self.salvar_regras()
        
        self.atualizar_lista_regras()
        self.cancelar_edicao()
    
    def cancelar_edicao(self):
        """Cancela o modo de edição"""
        self.editando_index = None
        self.limpar_campos_regra()
        self.btn_adicionar.config(state=tk.NORMAL)
        self.btn_editar.config(state=tk.DISABLED)
    
    def limpar_campos_regra(self):
        """Limpa todos os campos de entrada de regra"""
        self.entry_monitorar.delete(0, tk.END)
        self.entry_extensoes.delete(0, tk.END)
        self.entry_excecoes.delete(0, tk.END)
        self.entry_destino.delete(0, tk.END)
    
    def remover_regra(self):
        """Remove a regra selecionada"""
        selecionado = self.tree_regras.selection()
        if not selecionado:
            messagebox.showwarning("Aviso", "Selecione uma regra para remover!")
            return
        
        index = int(selecionado[0].lstrip('I'))
        
        # Operação thread-safe
        with self.regras_lock:
            if 0 <= index < len(self.regras):
                self.regras.pop(index)
                self.salvar_regras()
        
        self.atualizar_lista_regras()
        self.cancelar_edicao()
    
    def limpar_regras(self):
        """Remove todas as regras"""
        if messagebox.askyesno("Confirmar", "Deseja remover TODAS as regras?"):
            # Operação thread-safe
            with self.regras_lock:
                self.regras.clear()
                self.salvar_regras()
            
            self.atualizar_lista_regras()
            self.cancelar_edicao()
    
    def atualizar_lista_regras(self):
        """Atualiza a exibição da lista de regras"""
        # Limpar lista atual
        for item in self.tree_regras.get_children():
            self.tree_regras.delete(item)
        
        # Operação thread-safe
        with self.regras_lock:
            # Adicionar regras
            for i, regra in enumerate(self.regras):
                extensoes_str = ', '.join(regra['extensoes'])
                excecoes_str = ', '.join(regra['excecoes'])
                self.tree_regras.insert('', 'end', iid=f"I{i}", 
                                      values=(regra['monitorar'], extensoes_str, 
                                             excecoes_str, regra['destino']))
    
    def salvar_regras(self):
        """Salva as regras no arquivo JSON com tratamento de erro"""
        try:
            with open(self.arquivo_config, 'w', encoding='utf-8') as f:
                json.dump({'regras': self.regras}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            pass
    
    def carregar_regras(self):
        """Carrega as regras do arquivo JSON com tratamento de erro"""
        try:
            if os.path.exists(self.arquivo_config):
                with open(self.arquivo_config, 'r', encoding='utf-8') as f:
                    dados = json.load(f)
                    # Operação thread-safe
                    with self.regras_lock:
                        self.regras = dados.get('regras', [])
                self.atualizar_lista_regras()
        except:
            with self.regras_lock:
                self.regras = []
    
    def obter_todas_extensoes_de_outras_regras(self, regra_atual):
        """Obtém todas as extensões de todas as outras regras (exceto a atual)"""
        todas_extensoes = set()
        
        with self.regras_lock:
            for regra in self.regras:
                # Pular a regra atual para não auto-filtrar
                if regra == regra_atual:
                    continue
                    
                # Adicionar extensões da regra (exceto .tudo e .pasta)
                for ext in regra['extensoes']:
                    if ext not in ['.tudo', '.pasta']:
                        todas_extensoes.add(ext)
        
        return todas_extensoes
    
    def processar_regras(self):
        """Processa todas as regras ativas de forma segura"""
        if not self.regras or self.pausado:
            return
        
        # Cópia thread-safe das regras para processamento
        with self.regras_lock:
            regras_para_processar = self.regras.copy()
        
        for regra in regras_para_processar:
            self.processar_regra(regra)
    
    def processar_regra(self, regra):
        """Processa uma regra específica"""
        try:
            monitorar = Path(regra['monitorar'])
            destino = Path(regra['destino'])
            extensoes = regra['extensoes']
            excecoes = regra['excecoes']
            
            if not monitorar.exists():
                return
            
            # Garantir que pasta destino existe
            try:
                destino.mkdir(parents=True, exist_ok=True)
            except:
                return
            
            # Processar baseado nas extensões
            if '.tudo' in extensoes:
                self.mover_tudo_com_excecoes(monitorar, destino, excecoes, regra)
            else:
                self.mover_por_extensao_com_excecoes(monitorar, destino, extensoes, excecoes, regra)
                
        except:
            pass

    def mover_tudo_com_excecoes(self, origem, destino, excecoes, regra):
        """Move todos os arquivos e pastas, exceto as exceções"""
        try:
            for item in origem.iterdir():
                if self.arquivo_protegido(item.name):
                    continue
                
                # Verificar se item deve ser excluído considerando a regra atual
                if self.deve_excluir(item, excecoes, regra):
                    continue
                
                destino_item = destino / item.name
                
                if not destino_item.exists():
                    self.mover_item_seguro(item, destino)
        except:
            pass

    def mover_por_extensao_com_excecoes(self, origem, destino, extensoes, excecoes, regra):
        """Move arquivos baseado nas extensões, considerando exceções"""
        try:
            for item in origem.iterdir():
                if self.arquivo_protegido(item.name):
                    continue
                
                # Verificar se é pasta e se .pasta está nas extensões
                if item.is_dir() and '.pasta' in extensoes:
                    # Verificar se deve excluir considerando a regra atual
                    if not self.deve_excluir(item, excecoes, regra):
                        self.mover_item_seguro(item, destino)
                
                # Verificar extensões de arquivo
                elif item.is_file():
                    extensao_arquivo = item.suffix.lower()
                    
                    # Comportamento normal para todas as extensões
                    if extensao_arquivo in extensoes:
                        if not self.deve_excluir(item, excecoes, regra):
                            self.mover_item_seguro(item, destino)
        except:
            pass

    def arquivo_protegido(self, nome_arquivo):
        """Verifica se o arquivo/pasta é protegido (não deve ser movido)"""
        arquivos_protegidos = [os.path.basename(__file__), "config.json", "organizador.log"]
        return nome_arquivo in arquivos_protegidos

    def mover_item_seguro(self, item, destino):
        """Move um item de forma segura"""
        destino_item = destino / item.name
        
        if not destino_item.exists():
            try:
                # Lock para operações de arquivo
                with self.arquivo_lock:
                    shutil.move(str(item), str(destino))
                
                # Log apenas do movimento com nome e destino
                tipo = "Pasta" if item.is_dir() else "Arquivo"
                self.log_sistema(f"{tipo} movido: {item.name} para {destino}")
                
            except:
                pass

    def deve_excluir(self, item, excecoes, regra):
        """Verifica se o item deve ser excluído com base nas exceções e regras especiais"""
        # Verificar exceções normais (extensões)
        if item.is_file():
            extensao = item.suffix.lower()
            if extensao in excecoes:
                return True
            
            # 🔵 CORREÇÃO: .extensao_selecionadas agora é tratada como EXCEÇÃO
            if '.extensao_selecionadas' in excecoes:
                # Obter extensões de outras regras
                extensoes_outras_regras = self.obter_todas_extensoes_de_outras_regras(regra)
                
                # Excluir se a extensão estiver em outras regras
                if extensao in extensoes_outras_regras:
                    return True
                    
        elif item.is_dir():
            if '.pasta' in excecoes:
                return True
        
        # Verificar regra especial .pasta_selecionadas
        if '.pasta_selecionadas' in excecoes and item.is_dir():
            return self.pasta_eh_destino_em_outra_regra(item, regra)
        
        return False

    def pasta_eh_destino_em_outra_regra(self, pasta, regra_atual):
        """Verifica se uma pasta é usada como pasta de destino em outra regra"""
        try:
            caminho_pasta = str(pasta.resolve())
            
            with self.regras_lock:
                for regra in self.regras:
                    # Ignorar a regra atual
                    if regra == regra_atual:
                        continue
                    
                    caminho_destino_regra = str(Path(regra['destino']).resolve())
                    
                    # Verificar se a pasta é destino em outra regra
                    if caminho_pasta == caminho_destino_regra:
                        return True
                    
                    # Verificar se é subpasta de pasta de destino
                    if caminho_pasta.startswith(caminho_destino_regra + os.sep):
                        return True
            
            return False
        except:
            return False

    def log_sistema(self, mensagem):
        """Adiciona mensagem ao sistema de logging de forma thread-safe"""
        # Apenas mensagens permitidas são processadas
        mensagens_permitidas = [
            "Monitoramento iniciado",
            "Monitoramento PAUSADO", 
            "Monitoramento RETOMADO",
            "Arquivo movido:",
            "Pasta movida:"
        ]
        
        if any(permitida in mensagem for permitida in mensagens_permitidas):
            timestamp = time.strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {mensagem}"
            
            # Adicionar à queue para atualização da UI
            self.log_queue.put(log_entry)

    def processar_log_queue(self):
        """Processa mensagens da queue de log"""
        try:
            while True:
                mensagem = self.log_queue.get_nowait()
                self._atualizar_log_ui(mensagem)
        except Empty:
            pass
        
        # Agendar próxima verificação
        self.root.after(100, self.processar_log_queue)
    
    def _atualizar_log_ui(self, mensagem):
        """Atualiza o widget de log na thread principal"""
        self.text_log.insert(tk.END, mensagem + "\n")
        self.text_log.see(tk.END)
        
        # Limitar tamanho do log
        linhas = self.text_log.get(1.0, tk.END).split('\n')
        if len(linhas) > 500:
            self.text_log.delete(1.0, f"{len(linhas)-500}.0")
    
    def loop_monitoramento(self):
        """Loop principal de monitoramento a cada 10 segundos"""
        if self.monitorando:
            try:
                if not self.pausado:
                    self.processar_regras()
            except:
                pass
            
            # Agendar próxima verificação em 10 segundos
            self.root.after(10000, self.loop_monitoramento)
    
    def iniciar_monitoramento(self):
        """Inicia o loop de monitoramento"""
        self.monitorando = True
        self.log_sistema("Monitoramento iniciado")
        self.loop_monitoramento()
    
    def parar_monitoramento(self):
        """Para o loop de monitoramento"""
        self.monitorando = False
    
    def alternar_pausa(self):
        """Alterna entre pausado e ativo"""
        self.pausado = not self.pausado
        
        if self.pausado:
            self.status_var.set("Status: Monitoramento PAUSADO")
            self.btn_pausar.config(text="Retomar Monitoramento")
            self.log_sistema("Monitoramento PAUSADO")
        else:
            self.status_var.set("Status: Monitoramento ATIVO")
            self.btn_pausar.config(text="Pausar Monitoramento")
            self.log_sistema("Monitoramento RETOMADO")
        
        self.atualizar_menu_bandeja()
    
    def criar_icone_bandeja(self):
        """Cria um ícone simples para a bandeja do sistema"""
        imagem = Image.new('RGB', (64, 64), color='white')
        dc = ImageDraw.Draw(imagem)
        
        # Desenhar uma pasta simples
        dc.rectangle([10, 10, 54, 44], outline='blue', fill='lightblue', width=2)
        dc.rectangle([10, 10, 20, 16], outline='blue', fill='lightblue', width=2)
        
        return imagem
    
    def iniciar_bandeja_sistema(self):
        """Inicia o ícone na bandeja do sistema"""
        try:
            imagem = self.criar_icone_bandeja()
            
            # Menu será atualizado dinamicamente
            self.menu_bandeja = (
                pystray.MenuItem('Mostrar Janela', self.mostrar_janela),
                pystray.MenuItem('Pausar/Retomar', self.alternar_pausa),
                pystray.MenuItem('Encerrar', self.encerrar_aplicativo)
            )
            
            self.icone_bandeja = pystray.Icon('organizador_arquivos', imagem, 
                                            'Organizador de Arquivos', self.menu_bandeja)
            
            # Iniciar bandeja em thread separada
            thread_bandeja = threading.Thread(target=self.icone_bandeja.run, daemon=True)
            thread_bandeja.start()
            
        except:
            pass
    
    def atualizar_menu_bandeja(self):
        """Atualiza o texto do menu da bandeja para pausar/retomar"""
        if hasattr(self, 'icone_bandeja'):
            texto_pausa = "Retomar" if self.pausado else "Pausar"
            self.menu_bandeja = (
                pystray.MenuItem('Mostrar Janela', self.mostrar_janela),
                pystray.MenuItem(f'{texto_pausa} Monitoramento', self.alternar_pausa),
                pystray.MenuItem('Encerrar', self.encerrar_aplicativo)
            )
            self.icone_bandeja.menu = self.menu_bandeja
    
    def minimizar_para_bandeja(self):
        """Minimiza a janela para a bandeja do sistema"""
        self.root.withdraw()
    
    def mostrar_janela(self):
        """Mostra a janela principal"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def encerrar_aplicativo(self):
        """Encerra o aplicativo completamente"""
        self.parar_monitoramento()
        
        if hasattr(self, 'icone_bandeja'):
            try:
                self.icone_bandeja.stop()
            except:
                pass
        
        self.root.quit()
        self.root.destroy()

def main():
    """Função principal para iniciar o aplicativo"""
    try:
        root = tk.Tk()
        app = OrganizadorArquivos(root)
        root.mainloop()
    except Exception as e:
        print(f"ERRO ao iniciar aplicativo: {e}")

if __name__ == "__main__":
    main()