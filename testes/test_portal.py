import io
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ferramentas"))
import portal


class PortalTestes(unittest.TestCase):
    def test_codigo_correto_e_incorreto(self):
        registro = portal.hash_codigo("ABCD-1234")
        self.assertTrue(portal.conferir_codigo("ABCD-1234", registro))
        self.assertFalse(portal.conferir_codigo("ERRADO", registro))

    def test_zip_de_uma_pasta_e_achatado(self):
        memoria = io.BytesIO()
        with zipfile.ZipFile(memoria, "w") as z:
            z.writestr("exportacao/index.html", "<h1>Jogo</h1>")
            z.writestr("exportacao/assets/jogo.js", "console.log('ok')")
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "jogo"
            destino.mkdir()
            portal.extrair_zip_seguro(memoria.getvalue(), destino)
            self.assertTrue((destino / "index.html").is_file())
            self.assertTrue((destino / "assets" / "jogo.js").is_file())

    def test_zip_com_travessia_e_rejeitado(self):
        memoria = io.BytesIO()
        with zipfile.ZipFile(memoria, "w") as z:
            z.writestr("../fora.txt", "não pode")
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "jogo"
            destino.mkdir()
            with self.assertRaisesRegex(ValueError, "inseguro"):
                portal.extrair_zip_seguro(memoria.getvalue(), destino)


if __name__ == "__main__":
    unittest.main()
