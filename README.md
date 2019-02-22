# Github Explorer Server
_Victor Künstler & Friedrich Schöne_

## Abstract

## Overview
- [Setup](#setup)
- [ORM and Model Register](#orm-and-model-register)
- [Query Builder](#query-builder)
- [Custom Query Language](#custom-query-language)
- [HTTP Server](#http-server)

## Setup
In order to setup the server, install `pipenv` with `python3 -m pip install pipenv`.

Create a virtual python environment and install the pipenv requirements using `pipenv install`.

Enter the virtual environment with: `pipenv shell`.

In order to connect to the database and open the desired port for the webserver create a `.env` file in the project root folder and define the following environment variables:
- `PORT`: Defines the port the webserver should listen to.
- `PSQL_NAME`: Name of the postgres database.
- `PSQL_USER`: User name for the postgres database.
- `PSQL_PASSWORD`: User password for the postgres database

Start the server with: `python .`

## ORM and Model Register

## Query Builder

## Custom Query Language

## HTTP Server
