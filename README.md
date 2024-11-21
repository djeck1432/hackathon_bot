# Hackathon Bot

This project is a Django-based application designed to track GitHub repositories. The application provides an admin interface with custom functionalities such as per-user repositories tracking and referral link to our Telegram bot.
<hr>

## Features

- User-specific repositories tracking.
- Custom admin interface with enhanced features.
- Referral links for each repository.
<hr>

## Requirements

```
Git
Docker
Docker-Compose
```

# How it works:
<hr>

![An instruction image](docs/instructions.png)


`Here is a demo video how it works` [Click](https://drive.google.com/file/d/1DIh_qi31TtLu4YQ2SeFZc9y-NWDoQeTu/view?usp=drive_link)

## Installation

1. Clone the repository:
    ```sh
    git clone git@github.com:djeck1432/hackathon_bot.git
    ```

2. Change to the project directory:
    ```sh
    cd hackathon_bot
    ```

## Configuration

1. Create a `.env` file in the project directory and add your environment-specific variables.

    ```dotenv
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

## Usage

1. Build and run the application:
    ```sh
    docker-compose up -d --build
    ```

2. Open a web browser and go to [`http://127.0.0.1:80/`](http://127.0.0.1:80/) to access the admin interface.

3. Register and start using our app.
