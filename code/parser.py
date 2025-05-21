from docling.document_converter import DocumentConverter, FormatOption, ConversionResult, SimplePipeline
from docling.datamodel.pipeline_options import PipelineOptions, AcceleratorOptions
from docling.backend.docling_parse_v4_backend import DoclingParseV4DocumentBackend
from typing import Union, Any, Dict 
from pathlib import Path
import json
import logging



FILE_PATH = Path("/data/Тарифы 1_PKO.xlsx")

class Reader:
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.output_dir = Path("/data/")

    @staticmethod
    def _config() -> DocumentConverter:
        
        accelerator_options = AcceleratorOptions()
        accelerator_options.cuda_use_flash_attention2 = True
        accelerator_options.device = "cuda"
        
        pipeline_options = PipelineOptions()
        pipeline_options.accelerator_options = accelerator_options
        return DocumentConverter(format_options = {None:FormatOption(backend=DoclingParseV4DocumentBackend,
                                                                    pipeline_cls=SimplePipeline,
                                                                    pipeline_options=pipeline_options)})

    def pipeline(self) -> None:
        
        logger.info(f"Converting documents")
        conv_result = self.convert()
        
        exp_result = self.export(conv_result)
        json_result = self.filter(exp_result)

        json_path = Path(f"{self.output_dir}/updated.json")
        with json_path.open("w") as fp:
            logger.info("json dumping")
            json.dump(json_result, fp, indent=4)
        return None
        
    def convert(self, verbose: bool = False) -> ConversionResult:
        conv_result = self._config().convert(self.file_path)
        
        if verbose:
            _md_table = conv_result.document.export_to_markdown()
            print(_md_table)
            _json_table = conv_result.document.save_as_json(filename=f"{self.output_dir}/raw.json", indent=4)
        
        return conv_result

    def export(self, conv_result: ConversionResult, export_to_dict: bool = True) -> Union[str, Dict[str, Any]]:
        if export_to_dict:
            exp_result = conv_result.document.export_to_dict()
        else:
            exp_result = conv_result.document.export_to_html()
        return exp_result

    def filter(self, exp_result: Union[str, Dict[str, Any]]) -> Dict[str, str]:
        
        for _table in exp_result["tables"]:
            
            _headers = []
            _rows = []
            _n_col = int(_table["prov"][0]["bbox"]["r"])
            
            for _grid in _table["data"]["grid"]:
                for _cell in _grid:
                    if _cell["column_header"]:
                        _headers.append(_cell["text"])
                    else:
                        _rows.append(_cell["text"])

            _table = {}
            for i, _header in enumerate(_headers):
                for _row in _rows:
                    _table[_header] = _row[i + _n_col]
                    _rows = _rows[_n_col:]

        return _table

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    file = Reader(file_path=FILE_PATH)
    file.pipeline()

        
        