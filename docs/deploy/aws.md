<h1> Deploy on AWS </h1>

During instance creation please remember to add a Rule for port 80 forwarding HTTP and port 443 if planning to use HTTPS.

## Install docker

Please install docker following the [official docs](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository).


On Ubuntu machine the following commands will work:

```
sudo apt-get update
sudo apt install docker.io
sudo docker --version
```

## Install docker-compose

Please install docker-compose following the [official docs](https://docs.docker.com/compose/install/#install-compose-on-linux-systems)

On Linux machine the following commands will install `docker-compose`:

```
sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose

sudo chmod +x /usr/local/bin/docker-compose

sudo docker-compose version
```

## Provide notebooks

The easiest way to get notebooks on AWS EC2 machine is to use GitHub. My example repository is https://github.com/pplonski/mercury_demo_1

I clone it in the home directory in AWS EC2:

```
git clone https://github.com/pplonski/mercury_demo_1.git
```

## Get Mercury 

The next step is to get the Mercury code. Please run the following code in the home directory in AWS EC2:

```
git clone https://github.com/mljar/mercury.git
```

## Edit `.env` file

Please change directory to `mercury` and copy `.env.example` to `.env` file:

```
cd mercury
cp .env.example .env
```

Please edit the `.env` file and recommended changes:
- change `DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_PASSWORD`
- change `SECRET_KEY`
- change `ALLOWED_HOSTS` to your AWS EC2 machine public IP
- change `NOTEBOOKS_PATH` to point to your directory with notebooks

## Start docker-compose

You can start the Mercury with following command:

```
sudo docker-compose up --build -d
```

Please wait a while and you can open the browser with URL `http://your_public_IP` and you should see the Mercury app running. :)

To run the Pro version of Mercury please run:

```
sudo docker-compose -f docker-compose-pro.yml up --build -d
```

## Stop docker-compose

To stop the service:
```
sudo docker-compose down
```