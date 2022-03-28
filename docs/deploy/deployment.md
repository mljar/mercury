<h1> Deployment </h1>

There are two options to deploy Mercury. The first one is to use internal Django server. It is easy option and can be used for simple apps/demos. The second option is to use `docker-compose`.

## Deploy with `run` command

The prefered option for Heroku deployment. You deploy the Mercury with command:

```
mercury run
```

In Heroku you need to add `Procfile` file with the command instruction for `web` dyno:

```
web: mercury run 0.0.0.0:$PORT
```

Please remember to add the above `Procfile` to the GitHub repository. 

!!! important "Required packages"

    Before deployement, you need to add `requrements.txt` file with needed packages to the repository.

## Deploy with `docker-compose`

There is defined `docker-compose.yml` and `Dockerfiles` in `docker` directory in the Mercury [repository](https://github.com/mljar/mercury).

To build the containers:

```
docker-compose build
```

To run containers in detached mode:

```
docker-compose up -d
```

To stop containers:

```
docker-compose stop
```

The `docker-compose` version is using `nginx` server. 

## Deploy with `docker-compose` with Pro features

Please specify your GitHub personal access token in the `.env` file to enable Pro features.

To build containers:

```
docker-compose -f docker-compose-pro.yml build
```

To run containers in the detached mode:

```
docker-compose -f docker-compose-pro.yml up -d
```

To stop containers:

```
docker-compose -f docker-compose-pro.yml stop
```


