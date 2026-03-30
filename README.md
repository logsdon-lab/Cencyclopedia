# Cencyclopedia
Interactive centromere catalog.

<table>
  <tr>
    <td>
      <figure>
        <img src="docs/overview.png">
        <br>
        <figcaption>Centromere haplotypes</figcaption>
      </figure>
    </td>
    <td>
      <figure>
        <img src="docs/ui.png">
        <br>
        <figcaption>Phylogenetic tree</figcaption>
      </figure>
    </td>
  </tr>
</table>

## Getting Started
Clone repo.
```bash
git clone git@github.com:logsdon-lab/Cencyclopedia.git
cd Cencyclopedia
```

Setup dependencies. Requires Python >= 3.12.
```bash
python -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```


## Run locally
### Python
Set up app locally. Data is stored in repo.
```bash
python -m cencyclopedia.app
```

Then, open [`127.0.0.1:8050`](http://127.0.0.1:8050) in browser.

### Docker
Build the container and run app exposed on port 8050.
```bash
docker build -t cencyclopedia:latest .
docker run -p 8050:8050 --rm cencyclopedia:latest
```

Then, open [`127.0.0.1:8050`](http://127.0.0.1:8050) in browser.
