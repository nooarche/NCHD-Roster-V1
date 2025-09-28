FROM node:20-alpine AS build
WORKDIR /app
COPY package.json .              
RUN npm install                  
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=build /app/dist ./dist
RUN npm i serve@14.2.3
ENV PORT=5173
CMD ["npx", "serve", "-s", "dist", "-l", "5173"]
