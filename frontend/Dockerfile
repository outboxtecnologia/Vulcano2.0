# Build da SPA. VITE_API_BASE fica VAZIO por padrão: o nginx desta mesma imagem faz
# proxy de /api para o backend (nginx.conf), então o navegador chama a mesma origem —
# funciona igual por http e por https. Só preencha se a API for servida de outra origem,
# e nesse caso use https, senão o navegador bloqueia por mixed content.
FROM node:22-bookworm-slim AS build
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG VITE_API_BASE=
ENV VITE_API_BASE=${VITE_API_BASE}

RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
