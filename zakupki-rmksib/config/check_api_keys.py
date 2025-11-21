from config.settings import settings

def main():
    print("PERPLEXITY_API_KEY:", repr(settings.PERPLEXITY_API_KEY))
    print("SNIPER_SEARCH_BASE_URL:", repr(getattr(settings, 'SNIPER_SEARCH_BASE_URL', None)))

if __name__ == "__main__":
    main()
