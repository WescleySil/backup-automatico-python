# Automação de Backup pfSense & Google Drive

Este projeto consiste em scripts Python para automatizar o backup de configurações do pfSense e enviá-las para o Google Drive.

## Estrutura do Projeto

- `backup.py`: Script que acessa a interface web do pfSense via Selenium, faz login e baixa o arquivo de configuração XML mais recente.
- `gdrive.py`: Utilitário para enviar arquivos para uma pasta específica no Google Drive usando OAuth2.
- `files/`: Diretório local onde os backups baixados são armazenados temporariamente.

## Pré-requisitos

- Python 3.8 ou superior.
- Google Chrome instalado (o script usa o navegador para acessar o pfSense).
- Acesso ao painel administrativo do pfSense.
- Client ID, Client Secret e Refresh Token do Google Cloud (para acesso à API do Drive).

## Instalação

1. **Clone o repositório ou baixe os arquivos.**

2. **Crie um ambiente virtual (recomendado):**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/Mac:
   source .venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuração

1. **Variáveis de Ambiente:**
   Copie o arquivo de exemplo `.env.example` para um novo arquivo chamado `.env`:
   ```bash
   cp .env.example .env
   # ou no Windows:
   copy .env.example .env
   ```

2. **Edite o arquivo `.env` com suas credenciais:**
   - `PFSENSE_USER`: Usuário de acesso ao pfSense.
   - `PFSENSE_PASS`: Senha do usuáio.
   - `TARGET_URL`: (Opcional) URL de acesso ao pfSense. Padrão: `https://localhost`.
   - `BACKUP_FILENAME_PREFIX`: (Opcional) Prefixo do arquivo de backup (ex: `NOME_FIREWALL`).
   - `GDRIVE_FOLDER_ID`: ID da pasta no Google Drive onde os arquivos serão salvos (pode ser obtido na URL da pasta no navegador).
   **Autenticação via OAuth2 (Client ID & Secret)**
   - `GDRIVE_CLIENT_ID`: Seu Client ID do Google Cloud.
   - `GDRIVE_CLIENT_SECRET`: Seu Client Secret.
   - `GDRIVE_REFRESH_TOKEN`: Refresh Token para gerar tokens de acesso sem interação do usuário.

3. **Permissões no Google Drive:**
   - Certifique-se de que a conta que gerou o Refresh Token tem acesso de escrita à pasta.

## Como Usar

### 1. Realizar Backup e Upload (Fluxo Completo)
A maneira recomendada de rodar a automação é usando o script principal:
```bash
python main.py
```
Isso irá:
1. Conectar ao pfSense e baixar o backup.
2. Fazer o upload automático para o Google Drive.
3. Gerar logs detalhados no console e no arquivo `backup.txt`.

### 2. Execução manual (Scripts individuais)
Caso queira rodar etapas separadas:

**Backup do pfSense:**
Execute o script `backup.py` para baixar a configuração atual:
```bash
python backup.py
```
O arquivo será salvo na pasta `files/` com o nome formatado (ex: `PREFIXO - BKP_DD.MM.AAAA.xml`).

**Upload para o Google Drive:**
Use o script `gdrive.py`:
```bash
python gdrive.py "files/nome_do_arquivo.xml"
```

## Solução de Problemas

- **Verifique os Logs:** Se algo der errado ao rodar o `main.py`, verifique o arquivo `backup.txt` para detalhes do erro.
- **Erro de conexão ao pfSense:** Verifique se a URL (`TARGET_URL` no `.env`) corresponde ao endereço do seu firewall. O padrão é `https://localhost`.
- **Erro de SSL:** O script está configurado para ignorar erros de certificado (comum em setups locais), mas verifique se o Chrome não está bloqueando o acesso.
