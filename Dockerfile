# Use a Node.js base image
FROM node:18-alpine

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json to install dependencies
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the application
RUN npm run build

# Expose the port the app runs on (default from README is 37373)
EXPOSE 37373

# Command to run the application
# We'll use the 'mcp-hub' binary directly, assuming it's in dist/cli.js
# The port and config file will be passed via docker-compose.yml
CMD ["node", "dist/cli.js"]
