from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from pathlib import Path
import yt_dlp

class API():
    def __init__(self):
        pass


    def download(self, url: str, mode: int, outFolder: Path) -> None:
        if outFolder is None:
            outPath = Path("./out")
        else:
            outPath = Path(outFolder)

        ydl_opts = {
            'outtmpl': f'{outPath.absolute()}/%(title)s.%(ext)s',  # Automatically places file in out/ folder
            'quiet': True,
        }
        
        if mode == 0:
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
        elif mode == 1:
            ydl_opts.update({
                'format': 'bestvideo+bestaudio/best',
                'merge_output_format': 'mp4',
            })

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])


    def sanitizeYoutubeURL(self, url: str) -> str:
        """
        Removes playlist parameters (&list=, &index=, etc.) while preserving 
        the core video ID for standard, mobile, and shortened YouTube links.
        """
        try:
            parsed = urlparse(url)
            
            if "youtube.com" in parsed.netloc:
                query_params = parse_qs(parsed.query)
                
                if 'v' in query_params:
                    new_query = urlencode({'v': query_params['v'][0]})

                    return urlunparse(parsed._replace(query=new_query))

            elif "youtu.be" in parsed.netloc:
                return urlunparse(parsed._replace(query=""))

            elif "twitch.tv" in parsed.netloc:
                return urlunparse(parsed._replace(query=""))
            
        except Exception:
            pass
            
        return url

