# 1. Use an official Node.js runtime as a parent image
FROM node:22.6.0-alpine

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the package.json and package-lock.json
COPY package*.json ./

# 4. Install dependencies
RUN npm install

# 5. Copy the rest of your application
COPY . .

# 6. Expose the port the app runs on
EXPOSE 5173

# 7. Command to run the app
CMD ["npm", "run", "dev"]