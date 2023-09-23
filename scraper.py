from datetime import datetime
import httpx
import sys

AUTH_TOKEN = ""

if 'Bearer ' in AUTH_TOKEN:
    AUTH_TOKEN = AUTH_TOKEN.replace('Bearer ','')

# create HTTP client with browser-like user-agent:
client = httpx.Client(
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36",
    }
)


def get_guest_token():
    """register guest token for auth key"""
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "accept-encoding": "gzip",
        "accept-language": "en-US,en;q=0.5",
        "connection": "keep-alive",
        "Authorization": f"Bearer {AUTH_TOKEN}",
    }
    result = httpx.post(
        "https://api.twitter.com/1.1/guest/activate.json", headers=headers
    )
    guest_token = result.json()["guest_token"]  # e.g. '1622833653452804096'
    return guest_token


GUEST_TOKEN = get_guest_token()


def rest_id(handle: str):
    headers = {
        "authority": "api.twitter.com",
        "authorization": f"Bearer {AUTH_TOKEN}",
        "content-type": "application/json",
        "origin": "https://twitter.com",
        "referer": "https://twitter.com/",
        "x-guest-token": GUEST_TOKEN,
        "x-twitter-active-user": "yes",
        "x-twitter-client-language": "en",
    }
    url = f"https://api.twitter.com/graphql/lhB3zXD3M7e-VfBkR-5A8g/UserByScreenName?variables=%7B%22screen_name%22%3A%22{handle}%22%2C%22withSafetyModeUserFields%22%3Atrue%2C%22withSuperFollowsUserFields%22%3Atrue%7D&features=%7B%22responsive_web_twitter_blue_verified_badge_is_enabled%22%3Atrue%2C%22responsive_web_graphql_exclude_directive_enabled%22%3Afalse%2C%22verified_phone_label_enabled%22%3Afalse%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%7D"

    response = client.get(url, headers=headers)
    try:
        restId = response.json()["data"]["user"]["result"]["rest_id"]
    except Exception:
        return None
    return restId


def scrape_user(handle: str):
    headers = {
        "authority": "api.twitter.com",
        "authorization": f"Bearer {AUTH_TOKEN}",
        "content-type": "application/json",
        "origin": "https://twitter.com",
        "referer": "https://twitter.com/",
        "x-guest-token": GUEST_TOKEN,
        "x-twitter-active-user": "yes",
        "x-twitter-client-language": "en",
    }
    user_id = rest_id(handle)

    if not user_id:
        return f"{handle} not found"

    url = f"https://twitter.com/i/api/graphql/WzJjibAcDa-oCjCcLOotcg/UserTweets?variables=%7B%22userId%22%3A%22{user_id}%22%2C%22count%22%3A40%2C%22includePromotedContent%22%3Atrue%2C%22withQuickPromoteEligibilityTweetFields%22%3Atrue%2C%22withVoice%22%3Atrue%2C%22withV2Timeline%22%3Atrue%7D&features=%7B%22rweb_lists_timeline_redesign_enabled%22%3Afalse%2C%22blue_business_profile_image_shape_enabled%22%3Atrue%2C%22responsive_web_graphql_exclude_directive_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22creator_subscriptions_tweet_preview_api_enabled%22%3Afalse%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22tweetypie_unmention_optimization_enabled%22%3Atrue%2C%22vibe_api_enabled%22%3Atrue%2C%22responsive_web_edit_tweet_api_enabled%22%3Atrue%2C%22graphql_is_translatable_rweb_tweet_is_translatable_enabled%22%3Atrue%2C%22view_counts_everywhere_api_enabled%22%3Atrue%2C%22longform_notetweets_consumption_enabled%22%3Atrue%2C%22tweet_awards_web_tipping_enabled%22%3Afalse%2C%22freedom_of_speech_not_reach_fetch_enabled%22%3Atrue%2C%22standardized_nudges_misinfo%22%3Atrue%2C%22tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled%22%3Afalse%2C%22interactive_text_enabled%22%3Atrue%2C%22responsive_web_text_conversations_enabled%22%3Afalse%2C%22longform_notetweets_rich_text_read_enabled%22%3Atrue%2C%22longform_notetweets_inline_media_enabled%22%3Afalse%2C%22responsive_web_enhance_cards_enabled%22%3Afalse%7D"

    response = client.get(url, headers=headers)
    try:
        data = response.json()["data"]["user"]["result"]["timeline_v2"]["timeline"][
            "instructions"
        ]
        for item in data:
            if 'entries' in item:
                data = item['entries']
    except Exception as e:
        print(e)
        return f"{handle} is private user"
    doc = []
    for i in range(len(data)):
        try:
            doc.append(data[i]["content"]["itemContent"]["tweet_results"]["result"])
        except Exception:
            continue
    return doc


def serialize_tweet(docs: list):
    if type(docs) == str:
        return print(docs)
    result = []
    for doc in docs:
        try:
            from datetime import timedelta
            now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)-timedelta(days=30)
            try:
                twitter_date = datetime.strptime(
                    doc["legacy"]["created_at"], "%a %b %d %H:%M:%S +%f %Y"
                )
            except Exception as e:
                print('twitter date error',e)
                continue
            # if now >= twitter_date: #preprocess only today data
            #     print(now,'>=',twitter_date)
            #     continue
            try:
                images = [
                    x["media_url_https"]
                    for x in doc["legacy"]["extended_entities"]["media"]
                ]
            except Exception as e:
                print('get images error',e)
                images = None
            for user in doc["legacy"]["entities"]["user_mentions"]:
                # print("before", user)
                del user["id_str"]
                del user["indices"]
                # print("after", user)
            twit_top_dict = {
                "created_at": str(datetime.now()),
                "favorite_count": doc["legacy"]["favorite_count"],
                "followers_count": doc["core"]["user_results"]["result"]["legacy"][
                    "followers_count"
                ],
                "following_count": doc["core"]["user_results"]["result"]["legacy"][
                    "friends_count"
                ],
                "images": images,
                "in_reply_to": None,
                "in_reply_to_status_id_str": None,
                "keyword": None,
                "language": "id",
                "location": doc["core"]["user_results"]["result"]["legacy"]["location"],
                "name": doc["core"]["user_results"]["result"]["legacy"]["name"],
                "place": None,
                "profil_pic_url": doc["core"]["user_results"]["result"]["legacy"][
                    "profile_image_url_https"
                ],
                "retweet_count": doc["legacy"]["retweet_count"],
                "source": f"https://twitter.com/{doc['core']['user_results']['result']['legacy']['screen_name']}/status/{doc['rest_id']}",
                "statuses_count": None,
                "text": doc["legacy"]["full_text"],
                "tweet_id": doc["rest_id"],
                "twitter_date": twitter_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "user_description": doc["core"]["user_results"]["result"]["legacy"][
                    "description"
                ],
                "user_mentions": doc["legacy"]["entities"]["user_mentions"],
                "username": doc["core"]["user_results"]["result"]["legacy"][
                    "screen_name"
                ],
            }

            result.append(twit_top_dict)
        except Exception as e:
            print("serialize tweet error", e)
            print(doc)
    print("Tweet: ", len(result))
    return result


def scrap(main_acc: list):
    results = []

    main_acc = (
        main_acc
        if main_acc
        else [
            "Heraloebss",
        ]
    )

    related_acc = []

    # scrape main account
    for acc in main_acc:
        print("Scraping", acc)
        docs = scrape_user(acc)
        result = serialize_tweet(docs)
        if not result:
            continue
        for tweet in result:
            doc_id = tweet["tweet_id"]

            doc_index = {
                "_id": doc_id,
                "_source": tweet,
            }

            results.append(doc_index)

            # get related account from mentions
            if tweet["user_mentions"]:
                for user in tweet["user_mentions"]:
                    if (
                        user["screen_name"] not in related_acc
                        and user["screen_name"] not in main_acc
                    ):
                        related_acc.append(user["screen_name"])
            else:
                continue
        # get related account from quote tweet
        for doc in docs:
            try:
                user = doc["quoted_status_result"]["result"]["core"]["user_results"][
                    "result"
                ]["legacy"]["screen_name"]
                if user not in related_acc and user not in main_acc:
                    related_acc.append(user)
            except Exception:
                continue

        print("Total tweet: ", len(results))
    print("Related Account: ", len(related_acc))
    print("Related Account: ", related_acc)

    filename = '{}.json'.format(datetime.now().timestamp())
    with open(filename,'w') as w:
        import json
        json.dump(results,w)
    print(f'Save to: {filename}')

    return results

if __name__ == '__main__':
    # list_account = ['radityadika','BaseBDG']
    
    list_account = sys.argv[1:]
    scrap(list_account)
