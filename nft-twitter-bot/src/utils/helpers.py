def format_message(nft_name, nft_price, nft_link):
    return f"New NFT Listed: {nft_name} for {nft_price}! Check it out here: {nft_link}"

def handle_error(error):
    print(f"An error occurred: {error}")