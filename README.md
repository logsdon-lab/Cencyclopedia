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

## Browser
View in your browser at https://cencyclopedia.com.

## Run locally
### Python
Set up app locally. Data is stored in repo.
```bash
gunicorn -b 0.0.0.0:8050 'cencyclopedia.app:server()'
```

Then, open [`127.0.0.1:8050`](http://127.0.0.1:8050) in browser.

#### Data viewer only
To view just the centromere and dataviewer, create a copy of the configfile, `config.yaml:general.mode`.
```bash
cp config.yaml config_single.yaml
```

Modify `general.mode`, `general.output_regions`, and `general.selected_cen.height`.
```yaml
general:
  mode: single
  output_regions: data/bed_single.csv.gz
  selected_cen:
    height: 800
    vertical_spacing: 0.0
```

Then rerun pointing to the new configfile.
```bash
export CENCYCLOPEDIA_CONFIG="config_single.yaml"
gunicorn -b 0.0.0.0:8050 'cencyclopedia.app:server()'
```

### Docker
Build the container and run app exposed on port 8050.
```bash
docker build -t cencyclopedia:latest .
docker run -p 8050:8050 --rm cencyclopedia:latest
```

Then, open [`127.0.0.1:8050`](http://127.0.0.1:8050) in browser.
