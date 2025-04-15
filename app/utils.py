import httpx
from typing import List, Dict, Optional, Tuple, Any
import os
from dotenv import load_dotenv
import logging
from datura_py import Datura
from datetime import datetime, timedelta
from bittensor_wallet import Wallet
from bittensor import subtensor
from bittensor.utils.balance import Balance

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Datura client
datura = Datura(api_key=os.getenv("DATURA_API_KEY"))

# Initialize Subtensor
subtensor = subtensor(network="finney")  # Use Finney network instead of local

# Initialize wallet
wallet = Wallet()
wallet.create()


class Subtensor:
    def __init__(self):
        self.subtensor = subtensor
        self.wallet = wallet

    def get_tao_dividends(self, netuid: int, hotkey: str = "") -> Dict[str, float]:
        """
        Get Tao dividends for a subnet and hotkey.
        
        Args:
            netuid: The subnet ID
            hotkey: The hotkey address
            
        Returns:
            Dict[str, float]: Dictionary of hotkey to dividend amount
        """
        try:
            logger.info(f"Getting Tao dividends for netuid {netuid}, hotkey {hotkey}")
            
            # Query the chain for TaoDividendsPerSubnet
            result = self.subtensor.query_subtensor(
                "TaoDividendsPerSubnet",
                params=[netuid, hotkey]  # Provide both netuid and hotkey
            )
            
            if not result:
                logger.warning(f"No dividends found for netuid {netuid}")
                return {}
                
            # Process the result
            dividends = {}
            for key, value in result.items():
                if hotkey and key != hotkey:
                    continue
                dividends[key] = float(value)
                
            return dividends
            
        except Exception as e:
            logger.error(f"Error getting Tao dividends: {str(e)}")
            return {}

    def add_stake(self, netuid: int, hotkey: str, amount: float) -> bool:
        """
        Add stake to a hotkey.
        
        Args:
            netuid: The subnet ID
            hotkey: The hotkey address
            amount: Amount to stake in TAO
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate hotkey
            if not hotkey or hotkey.strip() == "":
                logger.error("Empty hotkey address provided")
                return False
                
            logger.info(f"Adding stake of {amount} TAO to hotkey {hotkey}")
            
            # Convert amount to Balance
            balance = Balance.from_tao(amount)
            
            # Call add_stake extrinsic
            success = self.subtensor.add_stake(
                wallet=self.wallet,
                hotkey_ss58=hotkey,
                amount=balance,
                wait_for_inclusion=True,
                wait_for_finalization=False
            )
            
            if success:
                logger.info(f"Successfully added stake of {amount} TAO")
            else:
                logger.error("Failed to add stake")
                
            return success
            
        except Exception as e:
            logger.error(f"Error adding stake: {str(e)}")
            return False

    def unstake(self, netuid: int, hotkey: str, amount: float) -> bool:
        """
        Remove stake from a hotkey.
        
        Args:
            netuid: The subnet ID
            hotkey: The hotkey address
            amount: Amount to unstake in TAO
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Removing stake of {amount} TAO from hotkey {hotkey}")
            
            # Convert amount to Balance
            balance = Balance.from_tao(amount)
            
            # Call unstake extrinsic
            success = self.subtensor.unstake(
                wallet=self.wallet,
                hotkey_ss58=hotkey,
                netuid=netuid,
                amount=balance,
                wait_for_inclusion=True,
                wait_for_finalization=False,
                safe_staking=True,
                allow_partial_stake=True,
                rate_tolerance=0.005
            )
            
            if success:
                logger.info(f"Successfully removed stake of {amount} TAO")
            else:
                logger.error("Failed to remove stake")
                
            return success
            
        except Exception as e:
            logger.error(f"Error removing stake: {str(e)}")
            return False


async def get_sentiment(netuid: int, hotkey: str = "") -> float:
# async def get_sentiment(netuid: int) -> float:
    """Get sentiment score for a subnet from Twitter data."""
    logger.info(f"Fetching sentiment for netuid: {netuid}")
    
    # Get Datura API key from environment
    datura_api_key = os.getenv("DATURA_API_KEY")
    if not datura_api_key:
        logger.error("DATURA_API_KEY not found in environment variables")
        raise ValueError("DATURA_API_KEY not configured")
    
    try:
        # Initialize Datura client
        datura = Datura(api_key=datura_api_key)
        
        # Calculate date range (last 30 days)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        # Search for tweets about the subnet
        result = datura.basic_twitter_search(
            query=f"Bittensor netuid {netuid}",
            sort="Top",
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            lang="en",
            verified=True,
            blue_verified=True,
            is_quote=True,
            is_video=True,
            is_image=True,
            min_retweets=1,
            min_replies=1,
            min_likes=1,
            count=10
        )
        
        if not result:
            logger.error("No tweets found in Datura search")
            raise ValueError("No tweets found for analysis")
            
        logger.info(f"Successfully fetched {len(result)} tweets from Datura")
        
        # Analyze sentiment using Chutes.ai
        sentiment_score = await analyze_sentiment(result)
        logger.info(f"Sentiment score for netuid {netuid}: {sentiment_score}")
        return sentiment_score
        
    except Exception as e:
        logger.error(f"Unexpected error in get_sentiment: {str(e)}")
        raise


async def analyze_sentiment(tweets: List[Dict]) -> float:
    """Analyze sentiment of tweets using Chutes.ai LLM."""
    logger.info(f"Analyzing sentiment for {len(tweets)} tweets")
    
    # Get Chutes API key from environment
    chutes_api_key = os.getenv("CHUTES_API_KEY")
    if not chutes_api_key:
        logger.error("CHUTES_API_KEY not found in environment variables")
        raise ValueError("CHUTES_API_KEY not configured")
    
    # Chutes API endpoint for LLM
    chutes_url = "https://llm.chutes.ai/v1/chat/completions"
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"Making request to Chutes API: {chutes_url}")
            
            # Combine all tweet texts
            combined_text = "\n".join([tweet.get("text", "") for tweet in tweets])
            
            # Prepare the request body
            request_body = {
                "model": "unsloth/Llama-3.2-3B-Instruct",
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            "Analyze the sentiment of these tweets about Bittensor. "
                            "Return a sentiment score between -100 (very negative) "
                            "and +100 (very positive). Consider the overall tone, "
                            "context, and implications of the tweets. Format your "
                            "response as a JSON object with a 'sentiment_score' field. "
                            f"Tweets are as follows:\n{combined_text}"
                        )
                    }
                ],
                "stream": False,
                "max_tokens": 1024,
                "temperature": 0.7
            }
            
            response = await client.post(
                chutes_url,
                json=request_body,
                headers={
                    "Authorization": f"Bearer {chutes_api_key}",
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Chutes API response: {data}")
            
            # Extract sentiment score from the response
            if "choices" not in data or not data["choices"]:
                logger.error("No choices found in Chutes API response")
                raise ValueError("Invalid response format from Chutes API")
            
            # Parse the JSON response from the LLM
            try:
                import json
                import re
                
                content = data["choices"][0]["message"]["content"]
                
                # Extract JSON from the content using regex
                json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                if not json_match:
                    logger.error("No JSON found in LLM response")
                    raise ValueError("Could not find JSON in LLM response")
                
                json_str = json_match.group(1)
                sentiment_data = json.loads(json_str)
                sentiment_score = float(sentiment_data["sentiment_score"])
                
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.error(f"Failed to parse sentiment score: {str(e)}")
                raise ValueError("Could not parse sentiment score from LLM response")
            
            logger.info(f"Successfully analyzed sentiment. Score: {sentiment_score}")
            return sentiment_score
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP error from Chutes API: {str(e)}")
        raise
    except httpx.RequestError as e:
        logger.error(f"Request error to Chutes API: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in analyze_sentiment: {str(e)}")
        raise


def perform_stake(netuid: int, hotkey: str, sentiment_score: float) -> bool:
    """
    Perform stake operation based on sentiment score.
    
    Args:
        netuid: The subnet ID
        hotkey: The hotkey address
        sentiment_score: Sentiment score between -100 and +100
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Performing stake operation for netuid {netuid}, hotkey {hotkey}")
        
        # Calculate stake amount based on sentiment
        stake_amount = abs(sentiment_score) * 0.01  # 0.01 TAO per sentiment point
        
        # Create Subtensor instance
        subtensor = Subtensor()
        
        # Perform stake/unstake based on sentiment
        if sentiment_score > 0:
            return subtensor.add_stake(netuid, hotkey, stake_amount)
        else:
            return subtensor.unstake(netuid, hotkey, stake_amount)
            
    except Exception as e:
        logger.error(f"Error performing stake operation: {str(e)}")
        return False
