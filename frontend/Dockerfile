FROM node:20-alpine AS build
WORKDIR /app
COPY package.json .              # only package.json for now
RUN npm install                  # use install (doesn't require package-lock.json)
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=build /app/dist ./dist
RUN npm i serve@14.2.3
ENV PORT=5173
CMD ["npx", "serve", "-s", "dist", "-l", "5173"]
