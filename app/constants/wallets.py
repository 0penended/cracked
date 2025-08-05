from dataclasses import dataclass
from typing import List


@dataclass
class Wallet:
    """Wallet information for tracking."""

    name: str
    address: str


# Solana wallets to track
SOLANA_WALLETS = [
    # Wallet("JID (pumpfun aper)", "3h65MmPZksoKKyEpEjnWU2Yk2iYT5oZDNitGy5cTaxoE"),
    # Wallet(
    #     "Y22 (500k to 5mil challenge)", "GgG65z3MXpmGnV3ZapKv5ayDqox1x7CJnqP1LD8FaZdt"
    # ),
    # Wallet(
    #     "Trippy (smart/eng investor)", "nPosUpnDtaB4dBaJUMF1bm78E4BTZDwWQWGoEmEyESx"
    # ),
    # Wallet("POW (KOL aper)", "8zFZHuSRuDpuAR7J6FzwyF3vKNx4CVW3DFHJerQhc7Zd"),
    # Wallet("Pnut Insider", "CKXzCmgNgQGonGvx9gpaHV9RXg1fHrMkQWmyzFuy4Cbv"),
    # Wallet("FrankDeGods (Kolscan #2)", "CRVidEDtEUTYZisCxBZkpELzhQc9eauMLR3FWg74tReL"),
    # Wallet("Cooker", "8deJ9xeUvXSJwicYptA9mHsU2rN2pDx37KWzkDkEXhU6"),
    # Wallet("AP (Kolscan #3)", "215nhcAHjQQGgwpQSJQ7zR26etbjjtVdW74NLzwEgQjP"),
    # Wallet("Euris (Kolscan #5)", "DfMxre4cKmvogbLrPigxmibVTTQDuzjdXojWzjCXXhzj"),
    # Wallet("TIL (Kolscan #6)", "EHg5YkU2SZBTvuT87rUsvxArGp3HLeye1fXaSDfuMyaf"),
    # Wallet("Danny (Kolscan #7)", "EaVboaPxFCYanjoNWdkxTbPvt57nhXGu5i6m9m6ZS2kK"),
    # Wallet("Lebron", "G5nxEXuFMfV74DSnsrSatqCW32F34XUnBeq3PfDS7w5E"),
    # Wallet("Smart wallet #1 (50% WR)", "2J4yED9RVQ9jEnj4t5AvKKVyxHH4eHiGxaLASy8mvPST"),
    # Wallet("Smart wallet #2 (40% WR)", "687kTFNvKG9GXf8UsPzyrKbKpz5ExNrSCWfs7S4PTGiL"),
    # Wallet("Smart wallet #3 (42% WR)", "dS8AzSWKkLunMja4CnAVBmJzpqTphfbqNQoQxPPagTv"),
    # Wallet("Smart wallet #4 (70% WR)", "GtyhzqA5ARhfMMn1weV7knuVMyYTJ2ipfVKrTGsjk7ZC"),
    # Wallet("Smart wallet #5 (75% WR)", "Efqoo7tUd9bhrA8kEZ6YhtBbo2mhr6VLAKzQEsBTyUsk"),
    # Wallet(
    #     "Pranav DD #1 (swing trading, long term holds)",
    #     "DNfuF1L62WWyW3pNakVkyGGFzVVhj4Yr52jSmdTyeBHm",
    # ),
    # Wallet(
    #     "Pranav DD #3 (low cap snipes but mid cap swings)",
    #     "4vw54BmAogeRV3vPKWyFet5yf8DTLcREzdSzx4rw9Ud9",
    # ),
    # Wallet(
    #     "Pranav DD #4 (snipes but mid caps swing trade. no high cap)",
    #     "EHg5YkU2SZBTvuT87rUsvxArGp3HLeye1fXaSDfuMyaf",
    # ),
    # Wallet(
    #     "Pranav DD #5 (Low to mid caps)", "DYAn4XpAkN5mhiXkRB7dGq4Jadnx6XYgu8L5b3WGhbrt"
    # ),
    # Wallet(
    #     "Pranav DD #6 (Low to mid caps)", "2CXbN6nuTTb4vCrtYM89SfQHMMKGPAW4mvFe6Ht4Yo6z"
    # ),
    # Wallet(
    #     "Pranav DD #7 (bit of everything)",
    #     "GfXQesPe3Zuwg8JhAt6Cg8euJDTVx751enp9EQQmhzPH",
    # ),
    # Wallet(
    #     "Pranav DD #8 (bit of everything low mid high swing trades)",
    #     "7ABz8qEFZTHPkovMDsmQkm64DZWN5wRtU7LEtD2ShkQ6",
    # ),
    # Wallet(
    #     "Pranav DD #9 (low to mid caps)", "BXNiM7pqt9Ld3b2Hc8iT3mA5bSwoe9CRrtkSUs15SLWN"
    # ),
    # Wallet(
    #     "Pranav DD #10 (swing trading mid caps)",
    #     "96sErVjEN7LNJ6Uvj63bdRWZxNuBngj56fnT9biHLKBf",
    # ),
    # Wallet(
    #     "Pranav DD #12 (low to mid caps)",
    #     "GJA1HEbxGnqBhBifH9uQauzXSB53to5rhDrzmKxhSU65",
    # ),
    # Wallet(
    #     "Pranav DD #13 (Snipe and swing mid caps)",
    #     "BCnqsPEtA1TkgednYEebRpkmwFRJDCjMQcKZMMtEdArc",
    # ),
    # Wallet(
    #     "Pranav DD #14 (low to mid caps)",
    #     "BD7oWkEQsUwE8sj4UT7jtrGjHC8Gq1iRqXY7U6DTbJpf",
    # ),
    # Wallet(
    #     "Pranav DD #15 (Solid snipes)", "7SDs3PjT2mswKQ7Zo4FTucn9gJdtuW4jaacPA65BseHS"
    # ),
    # Wallet("Pranav DD #17 (mixed bag)", "5TuiERc4X7EgZTxNmj8PHgzUAfNHZRLYHKp4DuiWevXv"),
    # Wallet(
    #     "Pranav DD #18 (Mix of low cap snipes and mid caps)",
    #     "CRVidEDtEUTYZisCxBZkpELzhQc9eauMLR3FWg74tReL",
    # ),
    # Wallet(
    #     "Pranav DD #19 (Swing trader trading on mid and high caps)",
    #     "ATFRUwvyMh61w2Ab6AZxUyxsAfiiuG1RqL6iv3Vi9q2B",
    # ),
    # Wallet("Pranav DD #20 (good mix)", "6S8GezkxYUfZy9JPtYnanbcZTMB87Wjt1qx3c6ELajKC"),
    # Wallet("PORTNOY", "5rkPDK4JnVAumgzeV2Zu8vjggMTtHdDtrsd5o9dhGZHD"),
    # Wallet("Bugha CT", "HABhDh9zrzf8mA4SBo1yro8M6AirH2hZdLNPpuvMH6iA"),
    # Wallet("Ansem Alt Maybe", "HYWo71Wk9PNDe5sBaRKazPnVyGnQDiwgXCFKvgAQ1ENp"),
    # Wallet("Gake (SMsol5/50%insidery)", "DNfuF1L62WWyW3pNakVkyGGFzVVhj4Yr52jSmdTyeBHm"),
    # Wallet("Devvy", "3tc4BVAdzjr1JpeZu6NAjLHyp4kK3iic7TexMBYGJ4Xk"),
    # Wallet("dk dd #1 oura", "4WPTQA7BB4iRdrPhgNpJihGcxKh8T43gLjMn5PbEVfQw"),
    # Wallet("dk dd #2 jijo", "4BdKaxN8G6ka4GYtQQWk4G4dZRUTX2vQH9GcXdBREFUk"),
    # Wallet("dk dd #3", "BieeZkdnBAgNYknzo3RH2vku7FcPkFZMZmRJANh2TpW"),
    # Wallet("dk dd #4 (700M of sol)", "GitYucwpNcg6Dx1Y15UQ9TQn8LZMX1uuqQNn8rXxEWNC"),
    # Wallet("DEX", "mW4PZB45isHmnjGkLpJvjKBzVS5NXzTJ8UDyug4gTsM"),
    # Wallet("BONK1", "5M8ACGKEXG1ojKDTMH3sMqhTihTgHYMSsZc6W8i7QW3Y"),
    # Wallet("BONK2", "5WRoMdhyQSuRRTAUkxjB8Cu3ss15d2e1Autvi6aGfF3s"),
    # Wallet("himgajria1", "94DFcTUgJ2Mf7r2RLiLdmHgqdgHZnndegS9RW2bxt51Q"),
    # Wallet("himgajria2", "BiozYn55Y7p1Sbi83n93zS3Tm5EHHXMGKC9EQfSvg2So"),
    # Wallet("himgajria3", "DBThRhtNc4kQ9dTWT5sW1RgcmEkiDNAJ5vohS8Ww5Aag"),
    # Wallet("himgajria4", "A1ECE86o3tz6UWmwMWicrqZmwRZ7RCRzmYYa9okNQRBw"),
    # Wallet("launchwhale1", "2QcJDFbfWCz1wjhsAT3PxL9PtKDdxzCZMyJRC5shzvQL"),
    # Wallet("launchwhale2", "BqMsLeiSBvNJUBtmZT8NFxQ41jjYpJSA63vxtorc4D17"),
    # Wallet("launchwhale3", "Hx19HmxpMW9wVySLstTGW9DJkMqSLwdkfpbhBankMyNH"),
    # Wallet("uselesswhale1", "FFtSpFy3WL5vFNu64RxVXsjNiBi1zJPSgXm8bbgZS5t8"),
    # Wallet("uselesswhale2", "EfxaH82BFWWj4xiY8hWsD5tTMnh6NAcsF19V6Xd6W9Gv"),
    # Wallet("uselesswhale3", "25CxFB3n1DwwnhQiaQesHH4RDrP1fpUdaPwtWKSkpmoK"),
]

# Hyperliquid wallets to track
HYPERLIQUID_WALLETS = [
    Wallet(
        "rank_1_30d_08_05_2025",
        "0x2ba553d9f990a3b66b03b2dc0d030dfc1c061036",
    ),
    Wallet(
        "rank_2_30d_08_05_2025",
        "0x7fdafde5cfb5465924316eced2d3715494c517d1",
    ),
    Wallet("rank_3_30d_08_05_2025", "0x15b325660a1c4a9582a7d834c31119c0cb9e3a42"),
    Wallet("rank_4_30d_08_05_2025", "0xd47587702a91731dc1089b5db0932cf820151a91"),
    Wallet("rank_5_30d_08_05_2025", "0x162cc7c861ebd0c06b3d72319201150482518185"),
    Wallet("rank_6_30d_08_05_2025", "0x044d0932b02f5045bc00e0a6818b7f98ef504681"),
    Wallet("rank_7_30d_08_05_2025", "0x716bd8d3337972db99995dda5c4b34d954a61d95"),
    Wallet("rank_8_30d_08_05_2025", "0x5e914f78c2711b47a9e62e342465aef2fa3b6515"),
    Wallet("rank_9_30d_08_05_2025", "0xec0b9ebf2a304c99cafe85c548c14dd7783cb078"),
    Wallet("rank_10_30d_08_05_2025", "0x020ca66c30bec2c4fe3861a94e4db4a498a35872"),
    Wallet("rank_11_30d_08_05_2025", "0x175e7023e8dc93d0c044852685ac33e856b577b4"),
    Wallet("rank_12_30d_08_05_2025", "0x1c020f03305acd09994c1910d440646e4a5f91b0"),
    Wallet("rank_13_30d_08_05_2025", "0xf83350f2426d9f4790b6aa61710f6a26ddd908e7"),
    Wallet("rank_14_30d_08_05_2025", "0x77c3ea550d2da44b120e55071f57a108f8dd5e45"),
    Wallet("rank_15_30d_08_05_2025", "0x4f7634c03ec4e87e14725c84913ade523c6fad5a"),
    Wallet("rank_16_30d_08_05_2025", "0xffbd3e51ae0e2c4407434e157965c064f2a11628"),
    Wallet("rank_17_30d_08_05_2025", "0x720a68bf0813853cd3ed74d2fd0f54edfc7a43e1"),
    Wallet("rank_18_30d_08_05_2025", "0x9794bbbc222b6b93c1417d01aa1ff06d42e5333b"),
    Wallet("rank_19_30d_08_05_2025", "0xb8b9e3097c8b1dddf9c5ea9d48a7ebeaf09d67d2"),
    Wallet("rank_20_30d_08_05_2025", "0x045bad6ba93375aab642f502c2c89851488c129f"),
    Wallet("rank_21_30d_08_05_2025", "0xff4cd3826ecee12acd4329aada4a2d3419fc463c"),
    Wallet("rank_22_30d_08_05_2025", "0xa312114b5795dff9b8db50474dd57701aa78ad1e"),
    Wallet("rank_23_30d_08_05_2025", "0xbf732ea04197942783e34730ed6e0f6099575d58"),
    Wallet("rank_24_30d_08_05_2025", "0x477296b8f5f5525be26e5c0a82eb0dd24da3949f"),
]


def get_solana_addresses() -> List[str]:
    """Get list of Solana wallet addresses."""
    return [wallet.address for wallet in SOLANA_WALLETS]


def get_hyperliquid_addresses() -> List[str]:
    """Get list of Hyperliquid wallet addresses."""
    return [wallet.address for wallet in HYPERLIQUID_WALLETS]
