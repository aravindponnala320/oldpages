FROM node:22-alpine

ARG APP_DIR
ENV NEXT_TELEMETRY_DISABLED=1

WORKDIR /app

RUN npm install -g npm@11.7.0

COPY package.json package-lock.json tsconfig.base.json eslint.config.mjs ./
COPY apps ./apps
COPY packages ./packages

RUN npm ci

EXPOSE 3000

CMD ["npm", "run", "dev"]
