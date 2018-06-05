
all:
	@echo "$(sep)Docker commands"
	@echo
	@echo 'For using Docker images'
	@echo
	@echo '- `make docker-build`:    Creates the image.'
	@echo '- `make docker-upload`:   Uploads the image.'
	@echo '- `make docker-clean`:    Removes all local images.'
	@echo
	@echo

tag=1

docker-build:
	sudo docker build -t andreacensi/mcdp:$(tag)        -f mcdp.Dockerfile ..
	sudo docker build -t andreacensi/mcdp_server:$(tag) -f mcdp_server.Dockerfile ..

docker-upload:
	sudo docker push andreacensi/mcdp:$(tag)
	sudo docker push andreacensi/mcdp_server:$(tag)

docker-clean:
	# Kill all running containers:
	-sudo docker kill $(shell sudo docker ps -q)

	# Delete all stopped containers (including data-only containers):
	-sudo docker rm $(shell sudo docker ps -a -q)

	# Delete all exited containers
	-sudo docker rm $(shell sudo docker ps -q -f status=exited)

	# Delete all images
	-sudo docker rmi $(shell sudo docker images -q)
