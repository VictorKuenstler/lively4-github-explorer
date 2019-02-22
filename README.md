# Github Explorer Server
_Victor Künstler & Friedrich Schöne_

## Abstract
Datasets are growing quickly but at the same time, data scientists create analyses that get more and more complex. Typically, exploring data involves a broad collection of different technologies, tools and it also requires several steps do extract interesting insights. For that reason, the process of building such a workflow until the actual exploration requires a lot of implementation time which often consists of the same steps which requires background knowledge about the data and programming skills.
To reduce this implementation overhead and the need for background knowledge, we developed a tool to explore the data schema, query the data and explore the resulting data visually for a database containing GitHub data (e.g. commits, projects, authors, comments). We abstracted the data and the relations between tables with the help of an ORM.
To support the exploration of the schemata, we developed a custom query language, which, in contrast to traditional SQL, supports a more natural way of exploring data and handling relationships between data.
We extended a code editor to suggest completions and provide examples for different fields and relations based on the preceding selections.
We also provide a data preview that let the user quickly review his or her query results. For the last step, the visualization, we implemented a tool that lets the user visualize the data. This tool allows to configure the data used by the individual visualizations but at the same time does not limit the user on preconfigured visualization.

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
