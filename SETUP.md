# Development Environment Setup

This guide explains how to start the development environment for the project using Docker Compose. It includes setting up the backend and database.

## Requirements

- Docker installed on your machine (v20+ recommended).
- Docker Compose installed (v20+ recommended).
- Ensure port **5433** is available for the PostgreSQL container.

## Starting the Development Environment

1. **Clone the Repository**

   ```sh
   git clone <repository-url>
   cd <repository-folder>
   ```

2. **Provide all required env variables**
Provide all variables from `.env.dev.example`   
```
# Django
SECRET_KEY=#

# PostgreSQL
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=#
DB_HOST=db

# Github
GITHUB_AUTH_TOKEN=#

# Telegram
TELEGRAM_BOT_TOKEN=#
```


3. **Build and Start Services**

   To build and run the entire development environment, use the following command:

   ```sh
   docker-compose -f docker-compose.dev.yaml up -d --build
   ```

   This command will:
   - Build the backend and DB Docker images.
   - Start the backend and PostgreSQL database containers.

4. **Access the Application**

   - **Backend API**: Accessible at [http://localhost:8000](http://localhost:8000).
   - **PostgreSQL Database**: Accessible at `localhost:5433` (make sure to use the `DB_USER` and `DB_PASSWORD` from the `.env` file).

## Stopping the Development Environment

To stop the environment and remove containers, use:

```sh
docker-compose -f docker-compose.dev.yaml down
```

This command stops all running containers and removes them, but the data volumes will persist.

## Rebuild or Update

If you have made changes to the code or Docker configuration, rebuild the containers:

```sh
docker-compose -f docker-compose.dev.yaml up -d --build
```

## How to create migration file:
1) Enter your virtual environment
2) Ensure you have installed poetry inside your venv
3) Install all dependencies
```
poetry install
```
4) Run command to create migration file
```
python manage.py makemigrations
```

### Apply Migrations
To apply migrations and update the database schema, use:
```bash
python manage.py migrate
```

### Revert Migrations
To revert the last migration, use:
```bash
python manage.py migrate app_name <previous_migration_name>
```
Replace `app_name` with the name of your app and `<previous_migration_name>` with the name of the migration you want to revert to.


## GitHub API Keys
To get a GitHub API key, follow these steps:
1. Go to [GitHub Settings](https://github.com/settings)
2. Navigate to [Developer settings](https://github.com/settings/developers)
3. Click on `Personal access tokens`
4. Generate a new token with the required scopes.

For more information, you can refer to the [GitHub documentation](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token).

## Telegram API Key
To get a Telegram API key, follow these steps:
1. Open Telegram and search for the [BotFather](https://telegram.me/BotFather)
2. Start a chat with BotFather and create a new bot using the `/newbot` command.
3. Follow the instructions to get your API token.
