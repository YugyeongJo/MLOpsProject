FROM node:16-alpine

WORKDIR /app

COPY app/package.json app/package-lock.json ./
RUN npm install
RUN cp -R node_modules /tmp/node_modules

COPY app/ .

RUN cp -R /tmp/node_modules ./

EXPOSE 3000

CMD ["npm", "start"]