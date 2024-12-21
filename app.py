# app.py
from flask import Flask, render_template, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import anthropic
import random
from typing import Dict, List
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
AD_CLIENT_ID = os.getenv('AD_CLIENT_ID')

# Rate limiting to prevent abuse
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

class LyricGenerator:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.styles = ["trap", "boom bap", "conscious", "melodic"]
        self.themes = ["success", "struggle", "love", "street life", "motivation"]
        
    def generate_prompt(self, style: str, theme: str, mood: str) -> str:
        return f"""Generate authentic rap lyrics in the style of {style} rap with a {theme} theme and {mood} mood. 
        The lyrics should be creative, include metaphors, and follow modern rap patterns. 
        Include 16 bars with complex rhyme schemes."""
    
    def analyze_complexity(self, lyrics: str) -> float:
        score = 0
        words = lyrics.split()
        
        # Check for multi-syllabic rhymes
        rhyme_patterns = self._find_rhyme_patterns(words)
        score += len(rhyme_patterns) * 0.5
        
        # Check for metaphors
        metaphor_indicators = ["like", "as", "metaphorically"]
        score += sum(lyrics.lower().count(ind) for ind in metaphor_indicators)
        
        # Check vocabulary diversity
        unique_words = len(set(words))
        total_words = len(words)
        score += (unique_words / total_words) * 10
        
        return min(score, 10)
    
    def _find_rhyme_patterns(self, words: List[str]) -> Dict[str, List[str]]:
        rhyme_dict = {}
        for word in words:
            if len(word) >= 3:
                ending = word[-2:]
                if ending in rhyme_dict:
                    rhyme_dict[ending].append(word)
                else:
                    rhyme_dict[ending] = [word]
        return {k: v for k, v in rhyme_dict.items() if len(v) > 1}
    
    async def generate_lyrics(self, style: str, theme: str, mood: str) -> Dict:
        prompt = self.generate_prompt(style, theme, mood)
        
        response = await self.client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            temperature=0.9,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        lyrics = response.content[0].text
        complexity_score = self.analyze_complexity(lyrics)
        
        return {
            "lyrics": lyrics,
            "complexity_score": complexity_score,
            "style": style,
            "theme": theme,
            "mood": mood
        }

generator = LyricGenerator(ANTHROPIC_API_KEY)

@app.route('/')
def index():
    return render_template('index.html', ad_client_id=AD_CLIENT_ID)

@app.route('/app')
def app_page():
    return render_template('app.html', ad_client_id=AD_CLIENT_ID)

@app.route('/api/generate', methods=['POST'])
async def generate():
    data = request.json
    style = data.get('style', 'trap')
    theme = data.get('theme', 'success')
    mood = data.get('mood', 'energetic')
    
    try:
        result = await generator.generate_lyrics(style, theme, mood)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
