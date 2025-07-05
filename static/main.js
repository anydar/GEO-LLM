document.addEventListener('DOMContentLoaded', () => {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-btn');
    let mapCounter = 0; // Counter for unique map IDs

    // Function to add a message to the chat
    function addMessage(content, isUser = false) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message');
        messageDiv.classList.add(isUser ? 'user-message' : 'bot-message');
        messageDiv.textContent = content;
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom of chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to add a formatted response
    function addFormattedResponse(content) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', 'bot-message');
        
        // Create answer div with direct formatting
        const answerDiv = document.createElement('div');
        answerDiv.classList.add('answer');
        
        // Clean up the content - remove any numbering or analysis indicators
        let cleanContent = content
            .replace(/^(Based on|According to|After) (my|the) analysis:?\s*/i, '')
            .replace(/^(Here is|Here's) (the|a|my) (answer|solution|response):?\s*/i, '')
            .replace(/^(Final|Direct) (answer|solution|response):?\s*/i, '')
            .trim();
            
        answerDiv.textContent = cleanContent;
        
        messageDiv.appendChild(answerDiv);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom of chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to show loading indicator
    function showLoading() {
        const loadingDiv = document.createElement('div');
        loadingDiv.classList.add('loading');
        loadingDiv.id = 'loading-indicator';
        
        const dotsDiv = document.createElement('div');
        dotsDiv.classList.add('loading-dots');
        
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            dotsDiv.appendChild(dot);
        }
        
        loadingDiv.appendChild(dotsDiv);
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Function to hide loading indicator
    function hideLoading() {
        const loadingIndicator = document.getElementById('loading-indicator');
        if (loadingIndicator) {
            loadingIndicator.remove();
        }
    }

    // Function to send message to backend
    async function sendMessage() {
        const message = userInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage(message, true);
        
        // Clear input
        userInput.value = '';
        
        // Show loading indicator
        showLoading();
        
        try {
            // Check if this is a direct tool command
            if (isToolCommand(message)) {
                await handleToolCommand(message);
            } else {
                // Regular LLM query
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ query: message })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    addMessage(`Error: ${data.error}`);
                } else {
                    addFormattedResponse(data.response);
                    
                    // Check if the message contains location names that could be geocoded
                    if (containsLocationQuery(message)) {
                        await tryGeocodeLocations(message);
                    }
                }
            }
            
            // Hide loading indicator
            hideLoading();
        } catch (error) {
            // Hide loading indicator
            hideLoading();
            
            addMessage(`Error: ${error.message}`);
        }
    }
    
    // Check if the message is a direct tool command
    function isToolCommand(message) {
        const toolCommands = [
            '/geocode',
            '/buffer',
            '/area',
            '/tool'
        ];
        
        return toolCommands.some(cmd => message.toLowerCase().startsWith(cmd));
    }
    
    // Handle direct tool commands
    async function handleToolCommand(message) {
        const parts = message.split(' ');
        const command = parts[0].toLowerCase();
        
        switch (command) {
            case '/geocode':
                if (parts.length < 2) {
                    addMessage('Usage: /geocode [location name]');
                    return;
                }
                const location = parts.slice(1).join(' ');
                await useGeocodeDirectly(location);
                break;
                
            case '/buffer':
                if (parts.length < 4) {
                    addMessage('Usage: /buffer [latitude] [longitude] [distance_km]');
                    return;
                }
                const lat = parseFloat(parts[1]);
                const lon = parseFloat(parts[2]);
                const distance = parseFloat(parts[3]);
                
                if (isNaN(lat) || isNaN(lon) || isNaN(distance)) {
                    addMessage('Error: Invalid coordinates or distance. Please use numeric values.');
                    return;
                }
                
                await useBufferDirectly(lat, lon, distance);
                break;
                
            case '/tool':
                if (parts.length < 3) {
                    addMessage('Usage: /tool [tool_name] [parameters as JSON]');
                    return;
                }
                
                const toolName = parts[1];
                const paramsText = parts.slice(2).join(' ');
                
                try {
                    const params = JSON.parse(paramsText);
                    await useToolDirectly(toolName, params);
                } catch (e) {
                    addMessage(`Error parsing parameters: ${e.message}`);
                }
                break;
                
            default:
                addMessage(`Unknown command: ${command}`);
        }
    }
    
    // Use geocode tool directly
    async function useGeocodeDirectly(location) {
        try {
            const response = await fetch('/api/geocode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ location })
            });
            
            const data = await response.json();
            
            if (data.error) {
                // Provide a more user-friendly error message
                if (data.error.includes("Could not geocode location")) {
                    addMessage(`❌ Location not found: "${location}". Please check the spelling or try a different location.`);
                } else {
                    addMessage(`❌ Error: ${data.error}`);
                }
            } else {
                const { lat, lon } = data.coordinates;
                addMessage(`📍 Location "${data.location}" coordinates: ${lat.toFixed(6)}, ${lon.toFixed(6)}`);
                
                // Create a map for the location
                createLocationMap(lat, lon, data.location);
            }
        } catch (error) {
            addMessage(`❌ Error: ${error.message}`);
        }
    }
    
    // Use buffer tool directly
    async function useBufferDirectly(lat, lon, distance_km) {
        try {
            const response = await fetch('/api/buffer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ lat, lon, distance_km })
            });
            
            const data = await response.json();
            
            if (data.error) {
                addMessage(`Error: ${data.error}`);
            } else {
                addMessage(`🔄 Created ${distance_km}km buffer around coordinates ${lat.toFixed(6)}, ${lon.toFixed(6)}`);
                // Here you could visualize the buffer on a map if you add a map component
            }
        } catch (error) {
            addMessage(`Error: ${error.message}`);
        }
    }
    
    // Use any tool directly
    async function useToolDirectly(toolName, params) {
        try {
            const response = await fetch('/api/tools', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ tool: toolName, params })
            });
            
            const data = await response.json();
            
            if (data.error) {
                addMessage(`Error: ${data.error}`);
            } else {
                addMessage(`🛠️ Tool "${toolName}" result: ${JSON.stringify(data.result, null, 2)}`);
            }
        } catch (error) {
            addMessage(`Error: ${error.message}`);
        }
    }
    
    // Check if a query contains a location reference
    function containsLocationQuery(query) {
        // Use our location extraction function
        const locationMatches = extractLocationNames(query);
        return locationMatches && locationMatches.length > 0;
    }
    
    // Try to geocode locations mentioned in the query
    async function tryGeocodeLocations(query) {
        // Extract potential location names from query
        const locationMatches = extractLocationNames(query);
        
        if (locationMatches && locationMatches.length > 0) {
            // Take the first location match (most likely the main location in query)
            const locationName = locationMatches[0];
            
            try {
                const response = await fetch('/api/geocode', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ location: locationName })
                });
                
                const data = await response.json();
                
                if (!data.error) {
                    const { lat, lon } = data.coordinates;
                    // Create a map for the location
                    createLocationMap(lat, lon, data.location);
                }
            } catch (error) {
                console.error("Error geocoding extracted location:", error);
                // Don't show error to user as this is an automatic enhancement
            }
        }
    }
    
    // Extract potential location names from text
    function extractLocationNames(text) {
        // This is a simple extraction - in a real app, you might use NER (Named Entity Recognition)
        const locationPatterns = [
            // Match "in [Location]" pattern (both capitalized and lowercase)
            /\bin\s+([A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+){0,3})/g,
            
            // Match "at [Location]" pattern
            /\bat\s+([A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+){0,3})/g,
            
            // Match "near [Location]" pattern
            /\bnear\s+([A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+){0,3})/g,
            
            // Match "around [Location]" pattern
            /\baround\s+([A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+){0,3})/g,
            
            // Match "of [Location]" pattern
            /\bof\s+([A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+){0,3})/g,
            
            // Match "[Location]" at beginning of sentence
            /(?:^|\.\s+)([A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+){0,3})\b/g
        ];
        
        // Add common Indian city names to directly match
        const indianCities = [
            'mumbai', 'delhi', 'bangalore', 'bengaluru', 'kolkata', 'chennai', 
            'hyderabad', 'pune', 'ahmedabad', 'jaipur', 'lucknow', 'kanpur', 
            'nagpur', 'indore', 'thane', 'bhopal', 'visakhapatnam', 'patna', 
            'vadodara', 'ghaziabad', 'ludhiana', 'coimbatore', 'madurai', 'nashik', 
            'varanasi', 'surat', 'agra', 'allahabad', 'howrah', 'gwalior', 'jabalpur', 
            'vijayawada', 'jodhpur', 'amritsar', 'kochi', 'mysore'
        ];
        
        let matches = [];
        
        // Try to match patterns
        for (const pattern of locationPatterns) {
            const patternMatches = [...text.matchAll(pattern)];
            for (const match of patternMatches) {
                if (match[1] && !isCommonWord(match[1])) {
                    matches.push(match[1]);
                }
            }
        }
        
        // Check for direct city mentions
        const textLower = text.toLowerCase();
        for (const city of indianCities) {
            if (textLower.includes(city)) {
                // Make sure it's a standalone word
                const regex = new RegExp(`\\b${city}\\b`, 'i');
                if (regex.test(textLower)) {
                    matches.push(city);
                }
            }
        }
        
        return matches;
    }
    
    // Check if a word is a common English word (not likely a location)
    function isCommonWord(word) {
        const commonWords = [
            "The", "This", "That", "These", "Those", "What", "Where", "When", "Why", "How",
            "There", "Here", "About", "Above", "Below", "Under", "Over", "Between", "Among",
            "Through", "During", "Before", "After", "Since", "Until", "While", "Because",
            "Although", "Unless", "Whether", "Whatever", "Whenever", "Wherever", "However"
        ];
        
        return commonWords.includes(word);
    }

    // Function to create a map for a geocoded location
    function createLocationMap(lat, lon, locationName) {
        mapCounter++;
        const mapId = `location-map-${mapCounter}`;
        
        // Create map container
        const mapContainer = document.createElement('div');
        mapContainer.classList.add('map-container');
        
        // Create map element
        const mapElement = document.createElement('div');
        mapElement.id = mapId;
        mapElement.classList.add('location-map');
        mapElement.style.height = '300px';
        mapElement.style.width = '100%';
        mapElement.style.marginTop = '10px';
        mapElement.style.borderRadius = '8px';
        mapElement.style.border = '1px solid #ddd';
        
        mapContainer.appendChild(mapElement);
        chatMessages.appendChild(mapContainer);
        
        // Create map
        const map = L.map(mapId).setView([lat, lon], 13);
        
        // Add tile layer (OpenStreetMap)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        
        // Add marker
        L.marker([lat, lon])
            .addTo(map)
            .bindPopup(`<b>${locationName}</b>`)
            .openPopup();
            
        // Scroll to bottom of chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    // Add welcome message
    addMessage('Welcome to the ISRO GeoLLM Assistant! Ask me any geospatial analysis question about India, and I\'ll provide a solution using ISRO tools and Indian datasets. This assistant is specifically designed for analyzing locations within India\'s geographic boundaries. You can also use direct tool commands like /geocode [location], /buffer [lat] [lon] [distance_km], or /tool [name] [params]');
});