# 🕰️ Time Capsule

Aplicação web para criar "cápsulas do tempo" digitais e físicas. Cápsulas digitais podem conter mensagens, fotos, vídeos e áudios, e só podem ser abertas em um local específico ou após uma data definida. Cápsulas físicas enviam um comando via MQTT para destravar um dispositivo IoT.

## ⚙️ Requisitos Funcionais (O QUE o sistema faz)
* **RF1** Cadastro/Login de Usuários: permite que usuários criem contas (com confirmação por email) ou façam login (email/senha).
* **RF2** Criar Cápsulas Digitais: inclusão de mensagens de texto, fotos, vídeos e áudios, escolhendo data e/ou local de liberação.
* **RF3** Criar Cápsulas Físicas: inclusão de uma mensagem e data de liberação para acionar um dispositivo IoT.
* **RF4** Geolocalização: validação de local correto (via GPS do navegador) para abrir cápsulas digitais baseadas em localização.
* **RF5** Temporizador: libera cápsulas (digitais e físicas) apenas após a data e hora especificadas.
* **RF6** Visualizar Cápsulas: listagem de todas as cápsulas criadas pelo usuário, mostrando seu status (bloqueada, disponível, física, etc.).
* **RF7** Publicação MQTT: O sistema publica uma mensagem JSON em um broker MQTT (HiveMQ) quando uma cápsula física atinge sua data de liberação.

## 🔧 Requisitos Não-Funcionais (COMO o sistema funciona)
* **RNF1** Performance: Tempo de carregamento rápido das páginas.
* **RNF2** Escalabilidade: Suporta múltiplos usuários simultâneos.
* **RNF3** Persistência de Dados: Garante que cápsulas e mídias não sejam perdidas, usando armazenamento de objetos e banco de dados.
* **RNF4** Deploy Contínuo: CI/CD automatizado via GitHub para Vercel (Frontend) e Render (Backend).
* **RNF5** Integração IoT: Comunicação segura com o broker MQTT usando TLS.
* **RNF6** Agendamento: O backend verifica cápsulas expiradas automaticamente a cada 60 segundos.

## 🚀 Funcionalidades Atuais
- **Cadastro de Usuários** (Supabase Auth) com confirmação por email.
- **Login de Usuários** (Supabase Auth + JWT no Backend).
- **Criar Cápsulas Digitais** com mensagens, fotos, vídeos ou áudios.
- **Criar Cápsulas Físicas (IoT)** que acionam um comando MQTT.
- **Upload de Mídias** (Supabase Storage) para os arquivos das cápsulas.
- **Validação de Geolocalização** (Leaflet API) para abertura.
- **Temporizador** (baseado em fuso horário local) para liberação.
- **Publicação MQTT** (Paho-MQTT + APScheduler) para cápsulas físicas expiradas.
- **Visualização de Cápsulas** com indicadores de tipo (Digital/Física) e status (Bloqueada/Disponível).

## 🛠️ Tecnologias
| Área | Tecnologias |
| :--- | :--- |
| **Frontend** | Vue.js, Vite, Vercel |
| **Backend** | Flask (Python), Gunicorn, Render |
| **Banco de Dados** | Supabase (PostgreSQL) |
| **Armazenamento** | Supabase Storage (para fotos, vídeos, áudios) |
| **APIs & Protocolos** | Leaflet (OpenStreetMap), MQTT (HiveMQ Broker) |

### Bibliotecas Principais
* **Backend:** `Flask-APScheduler` (Agendamento de tarefas), `paho-mqtt` (Cliente MQTT), `Flask-JWT-Extended` (Autenticação).
* **Frontend:** `axios` (Requisições HTTP), `date-fns` (Formatação de data e fuso), `leaflet` (Mapas).