# What political impact does social media have?

## Description
The motivation behind our project is that social media is a big part of today's life and becomes more and more political by different political opinions that are spreaded. Therefore, our project is based on the main question "What political impact does social media have?" and the research questions explore several movements and trends that can be found on Youtube. 

### Research questions
The seven research questions we worked on are:
1. How has the public perception of anti-vaccine conspiracy via YouTube changed during the last five years? 
2. To what extent do spikes in Wikipedia pageviews related to the AfD align with increases in YouTube video uploads about the party during German federal elections?
3. In what ways has social media contributed to the growth and visibility of the Fridays for Future climate movement? 
4. How did public interest and sentiment in the #MeToo movement evolve over time?
5. How has the perception of Sahra Wagenknecht's presence on social media changed in the past before and after founding her own party?
6. To what extent does the number of social media posts (on YouTube) by political parties influence election results?
7. How has public opinions about the ‘tradwife’ movement evolved since its beginning in 2020?

### Project structure
The answer/code for each question can be found within the according folder. <br>
For example, the answer for the first question is found in the 📂 [Question1 folder](./Question1). The contents include (at least) one JupyterNotebook that contains the code, as well as CSV containing data. Furthermore, some folders contain images of created graphics. <br>

### LLM usage
We used LLMs to gather keywords (KeyBERT), filter out stopwords (spaCy) and calculate sentiment (VADER). In the code, we clearly indicate (through comments) where each LLM or library is applied.<br> 
Additionally, we used LLMs to help rewrite and translate text for our website/poster from German to English. <br>
Furthermore, LLMs were used to help with setting up APIs. 


## Getting started

### How to get the API keys
**How to get the YouTube API key:** <br> 
To get an API key for YouTube, you first need a Google account. <br> 
Then you have to visit https://console.developers.google.com/, where you have to create a project. <br> 
After this, navigate to the credentials section. <br> 
![credentials section](image.png) <br> 

Finally, click on create credentials and create an API key. <br> 
![create API key](image-1.png)



**WikiMedia/WikiPedia API:**<br>
The WikiMedia API does not require an API key. Instead, a header is required that identifies the script (which is given in our code).


### How to install our Python environment
1. Open terminal in the project directory.
2. Run pipenv shell.
3. Install pandas, numpy, spacy, matplotlib, requests, vaderSentiment, seaborn, wordcloud, keybert and google-api-python-client.
4. Install the requirements from requirements.txt.

### How to install Docker
1. Visit https://www.docker.com/products/docker-desktop/ and click on "Download Docker Desktop". <br>
2. Choose the version fitting for your Operating System.<br>
3. Install the program and start it to check if any errors occur. <br>
4. Optional: open a terminal and run 
```docker --version```.
This should print the Docker version you have installed.

### How to Start the Website

1. **Start [Docker Desktop](https://www.docker.com/products/docker-desktop/)**  
2. In the terminal, navigate to the project directory:  
    ```bash
    cd newDataDiva/DataDivas/Website
    ```
   📂 [Open project folder](./Sonja/Website)  
3. Start the Docker environment (including build):  
    ```bash
    docker compose up --build
    ```
for initial build run: [Windows](/initialStart.bat) or [Linux/Mac](/initialStart.sh)
or run this script instead: [Windows](/start.bat) or [Linux/Mac](/start.sh)

## Authors
**DataDivas** <br>
Sonja Waldenspuhl - stu235521@mail.uni-kiel.de <br>
Maja Kahl - stu240340@mail.uni-kiel.de <br>
Diana Kuznecov - stu240382@mail.uni-kiel.de <br>
Carolin Delfs - stu241068@mail.uni-kiel.de <br>

## Sources
1. Youtube API - https://developers.google.com/youtube/v3/docs
2. MeToo movement - https://en.wikipedia.org/wiki/MeToo_movement
3. Bundeswahlleiterin - https://www.bundeswahlleiterin.de/
4. Tradwife - https://en.wikipedia.org/wiki/Tradwife
5. Wikimedia API - https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/
6. List of school climate strikes - https://en.wikipedia.org/wiki/List_of_school_climate_strikes
