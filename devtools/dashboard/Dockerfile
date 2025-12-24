FROM node:20-alpine

RUN apk add --no-cache docker-cli docker-cli-compose curl

WORKDIR /app

COPY package*.json ./
RUN npm install --production

COPY . .

EXPOSE 7331

CMD ["node", "src/server.js"]
