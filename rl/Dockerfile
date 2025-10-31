FROM debian:stable-slim

RUN apt-get update && apt-get install -y cowsay && apt-get clean

# cowsay est installé dans /usr/games
ENV PATH="/usr/games:${PATH}"

ENV MESSAGE="Bonjour, je suis une vache Docker !"

CMD cowsay "$MESSAGE"










