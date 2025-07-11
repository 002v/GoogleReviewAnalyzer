import re
from typing import Optional, Dict, Any

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.dates import DateFormatter
from textblob import TextBlob
from wordcloud import WordCloud
import dateparser
from pathlib import Path

# --- Configuration & Defaults ---
WC_DEFAULTS = {
    'width': 800,
    'height': 400,
    'stopwords': 'english',
    'min_font_size': 10,
    'max_words': 200,
    'background_color': 'black',
    'colormap': 'viridis',
}

DATE_FORMAT = '%Y'
DEFAULT_ROLLING_WINDOW_DAYS = 7
DEFAULT_PALETTE = "colorblind"


# --- Helper Functions ---

def parse_relative_date(date_str: str) -> Optional[pd.Timestamp]:
    """
    Convert relative date strings (with optional 'Edited' prefix) to Timestamp.
    Returns None if parsing fails.
    """
    clean = re.sub(r'^Edited\s+', '', date_str.strip())
    dt = dateparser.parse(clean)
    return pd.to_datetime(dt) if dt else None


def parse_rating(rating_str: str) -> Optional[float]:
    """
    Convert 'x/5' style rating to float x. Returns None for invalid formats.
    """
    try:
        return float(rating_str.split('/')[0])
    except (AttributeError, ValueError, IndexError):
        return None


def _apply_style(bg_color: str = 'white') -> None:
    """
    Apply clean, readable style with custom colors for the specified background.
    """
    sns.set_style('whitegrid', {
        'axes.facecolor': bg_color,
        'figure.facecolor': bg_color,
        'grid.color': '#444444' if bg_color == 'black' else '#cccccc',
        'axes.edgecolor': 'white' if bg_color == 'black' else 'black'
    })

    text_color = 'white' if bg_color == 'black' else 'black'
    plt.rcParams.update({
        'text.color': text_color,
        'axes.labelcolor': text_color,
        'xtick.color': text_color,
        'ytick.color': text_color,
        'axes.edgecolor': text_color,
        'legend.facecolor': '#222222' if bg_color == 'black' else 'white',
        'legend.edgecolor': text_color,
        'axes.titlesize': 12,
        'figure.titlesize': 14
    })


# --- Main Visualization Function ---

def visualize(
        filename: str,
        rolling_window_days: int = DEFAULT_ROLLING_WINDOW_DAYS,
        background_color: str = 'black',
        output_path: Optional[str] = None,
        plot_config: Optional[Dict[str, Any]] = None
) -> plt.Figure:
    """
    Create comprehensive review analysis visualization from JSON data.

    Parameters:
    -----------
    filename : str
        Path to JSON file containing review data
    rolling_window_days : int
        Window size (days) for rolling averages
    background_color : str
        Background color for plots and word cloud
    output_path : Optional[str]
        Path to save output figure (if provided)
    plot_config : Optional[Dict]
        Custom configuration for plot elements

    Returns:
    --------
    plt.Figure
        Matplotlib Figure object containing all visualizations
    """
    # --- Data Loading & Preparation ---
    df = pd.read_json(filename)
    df['date'] = df['date'].apply(parse_relative_date)
    df['rating'] = df['rating'].apply(parse_rating)
    df.dropna(subset=['date', 'rating', 'text'], inplace=True)

    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').set_index('date')
    df = df[df.index <= pd.Timestamp.now()]

    # --- Feature Engineering ---
    df['raw_sentiment'] = df['text'].apply(
        lambda t: TextBlob(str(t)).sentiment.polarity
    )
    df['rating_smooth'] = df['rating'].rolling(f'{rolling_window_days}D').mean()
    df['sent_smooth'] = df['raw_sentiment'].rolling(f'{rolling_window_days}D').mean()

    # --- Style & Layout Setup ---
    _apply_style(bg_color=background_color)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10),
                             gridspec_kw={'width_ratios': [3, 2]})
    date_fmt = DateFormatter(DATE_FORMAT)
    palette = sns.color_palette(DEFAULT_PALETTE, 4)

    # --- Plot 1: Rating Over Time ---
    ax = axes[0, 0]
    ax.plot(df.index, df['rating'], marker='o', alpha=0.3,
            label='Raw Ratings', color=palette[0])
    ax.plot(df.index, df['rating_smooth'], linewidth=2,
            label=f'{rolling_window_days}-Day Average', color=palette[1])
    ax.axhline(df['rating'].mean(), color='gray', linestyle='--', label='Overall Mean')

    ax.set_title('Rating Trends Over Time')
    ax.set_ylabel('Rating (1-5)')
    ax.legend(loc='upper left')
    ax.xaxis.set_major_formatter(date_fmt)
    ax.tick_params(axis='x', rotation=45)

    # --- Plot 2: Rating Distribution ---
    ax = axes[0, 1]
    sns.histplot(df['rating'], bins=5, kde=True, ax=ax, color=palette[0])
    ax.set_title('Rating Distribution')
    ax.set_xlabel('Rating')
    ax.set_ylabel('Number of Reviews')

    # --- Plot 3: Sentiment Analysis ---
    ax = axes[1, 0]
    ax.plot(df.index, df['raw_sentiment'], marker='o', alpha=0.3,
            label='Raw Sentiment', color=palette[2])
    ax.plot(df.index, df['sent_smooth'], linewidth=2,
            label=f'{rolling_window_days}-Day Average', color=palette[3])
    ax.axhline(0, color='gray', linestyle='--')

    ax.set_title('Sentiment Polarity Trends')
    ax.set_ylabel('Polarity (-1 to +1)')
    ax.legend(loc='upper left')
    ax.xaxis.set_major_formatter(date_fmt)
    ax.tick_params(axis='x', rotation=45)

    # --- Plot 4: Word Cloud ---
    ax = axes[1, 1]
    text = ' '.join(df['text'].str.lower())

    # Merge default settings with user overrides
    wc_settings = WC_DEFAULTS.copy()
    wc_settings.update({
        'background_color': background_color,
        'colormap': 'plasma' if background_color == 'black' else 'viridis'
    })

    if plot_config and 'wordcloud' in plot_config:
        wc_settings.update(plot_config['wordcloud'])

    wc = WordCloud(**wc_settings).generate(text)
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    ax.set_title('Common Terms in Reviews')

    # --- Final Touches ---
    fig.suptitle('Customer Feedback Analysis Dashboard', fontsize=16, y=1)
    plt.tight_layout()

    if output_path:
        out = Path(output_path)
        fig.savefig(str(out), dpi=300, facecolor=background_color)
    return fig


