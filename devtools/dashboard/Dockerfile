FROM node:20-alpine

WORKDIR /app

RUN apk add --no-cache docker-cli docker-cli-compose curl

COPY package*.json ./
RUN npm install --production

COPY . .

EXPOSE 7331

CMD ["npm", "start"]
