# File Organizer Auto

**Organizador automático de arquivos com regras flexíveis e interface gráfica**
**Automatic file organizer with flexible rules and graphical interface**

---

# 📖 Descrição / Description

## 🇧🇷 Português

O **File Organizer Auto** é um aplicativo desenvolvido em Python que monitora pastas do seu computador e move automaticamente arquivos e pastas para locais de destino com base em regras definidas por você.

Ele permite criar regras personalizadas, como:

* mover todos os arquivos de uma pasta
* mover apenas determinados tipos de arquivo
* aplicar exceções
* evitar conflitos entre regras

Tudo isso com uma **interface gráfica simples** e um **ícone na bandeja do sistema** para facilitar o acesso.

---

## 🇺🇸 English

**File Organizer Auto** is a Python application that monitors folders on your computer and automatically moves files and folders to destination locations based on rules you define.

You can create custom rules such as:

* moving everything from a folder
* moving only specific file types
* applying exceptions
* avoiding rule conflicts

All of this with a **simple graphical interface** and a **system tray icon** for easy access.

---

# ✨ Funcionalidades / Features

* Interface gráfica amigável (**Tkinter**)
* Criação de múltiplas regras de organização
* Monitoramento automático de pastas
* Suporte a extensões especiais
* Sistema de exceções
* Persistência das regras em `config.json`
* Monitoramento contínuo (a cada 10 segundos)
* Pausar / retomar monitoramento
* Ícone na bandeja do sistema
* Log de atividades em tempo real
* Operação **thread-safe** para evitar conflitos
* Validação de caminhos e extensões

---

# 📦 Instalação / Installation

## Pré-requisitos / Prerequisites

* **Python 3.6+** (recomendado 3.8+)
* **Windows** (testado no Windows)

---

## Passos / Steps

### 1️⃣ Clone o repositório

```bash
git clone https://github.com/seu-usuario/file-organizer-auto.git
cd file-organizer-auto
```

### 2️⃣ Instale as dependências

```bash
pip install -r requirements.txt
```

> O **tkinter** já vem instalado com o Python na maioria das distribuições.

---

### 3️⃣ Execute o programa

```bash
python "Auto organizador.py"
```

---

# 🔧 Como usar / How to use

## 1️⃣ Tela principal

Ao iniciar o programa você verá:

* campos para criar regras
* lista de regras existentes
* log de atividades

---

## 2️⃣ Criando uma regra

### 🇧🇷 Português

**Pasta Monitorada**

Selecione a pasta que será observada.

Exemplo:

```
D:/Documentos
```

**Extensões**

Digite extensões separadas por vírgula.

Exemplos:

```
.pdf, .docx, .jpg
```

Extensões especiais:

```
.tudo
.pasta
```

**Exceção**

Extensões que **não devem ser movidas**.

Exemplo:

```
.tmp, .log
```

Exceções especiais:

```
.pasta_selecionadas
.extensao_selecionadas
```

**Pasta Destino**

Escolha onde os arquivos serão movidos.

Se não existir, será criada automaticamente.

Clique em **Adicionar Regra**.

---

### 🇺🇸 English

**Monitored Folder**

Choose the folder that will be watched.

Example:

```
D:/Documents
```

**Extensions**

Type file extensions separated by commas.

Example:

```
.pdf, .docx, .jpg
```

Special extensions:

```
.tudo
.pasta
```

**Exception**

Extensions that should **not be moved**.

Example:

```
.tmp, .log
```

Special exceptions:

```
.pasta_selecionadas
.extensao_selecionadas
```

**Destination Folder**

Choose where files will be moved.

If the folder does not exist, it will be created automatically.

Click **Add Rule**.

---

# 🧠 Extensões especiais / Special extensions

| Extensão                 | Significado                                         |
| ------------------------ | --------------------------------------------------- |
| `.tudo`                  | Move todos os arquivos e pastas                     |
| `.pasta`                 | Move pastas inteiras                                |
| `.pasta_selecionadas`    | Evita mover pastas que são destino de outras regras |
| `.extensao_selecionadas` | Evita mover extensões usadas em outras regras       |

---

# 📁 Estrutura do projeto

```
file-organizer-auto/
│
├── Auto organizador.py
├── config.json
├── organizador.log
├── README.md
└── requirements.txt
```

`config.json` e `organizador.log` são criados automaticamente.

---

# 🚀 Gerando executável (.exe)

## 1️⃣ Instale o PyInstaller

```bash
pip install pyinstaller
```

---

## 2️⃣ Vá para a pasta do projeto

```bash
cd caminho\para\file-organizer-auto
```

---

## 3️⃣ Gere o executável

```bash
pyinstaller --onefile --windowed "Auto organizador.py"
```

Opcional:

```bash
pyinstaller --onefile --windowed --icon=icone.ico "Auto organizador.py"
```

---

## 4️⃣ Localize o executável

O `.exe` será criado na pasta:

```
dist/
```

Ele pode ser executado **mesmo sem Python instalado**.

---

# 🖥️ Plataformas suportadas

* Windows 10
* Windows 11

[Inference]
Pode funcionar em Linux e macOS, mas não foi testado.

---

# 📄 Licença

Este projeto está licenciado sob a **MIT License**.

---

# 🤝 Contribuição

Contribuições não estão sendo aceitas no momento.

Você pode fazer um **fork** e adaptar para seu uso.

---

# 📧 Contato

Se tiver dúvidas ou sugestões, abra uma **issue no GitHub**.

---

⭐ Aproveite e mantenha seus arquivos sempre organizados!
