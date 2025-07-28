from docling.document_converter import (
    DocumentConverter,
    FormatOption,
    ConversionResult,
    SimplePipeline,
)
from docling.datamodel.pipeline_options import PipelineOptions, AcceleratorOptions
from docling.backend.docling_parse_v4_backend import DoclingParseV4DocumentBackend
from docling.datamodel.base_models import ConversionStatus
from typing import Union, Any, Dict, Iterable, List
from pathlib import Path
import json
import logging


class Reader:

    def __init__(
        self,
        file_path: Path,
        output_dir: Path = Path("/data/updated"),
        verbose: bool = False,
    ):
        self.file_path = list(file_path.glob("*.xlsx"))
        self.output_dir = output_dir
        self.verbose = verbose

    @staticmethod
    def _config() -> DocumentConverter:

        accelerator_options = AcceleratorOptions()
        accelerator_options.cuda_use_flash_attention2 = True
        accelerator_options.device = "cuda"

        pipeline_options = PipelineOptions()
        pipeline_options.accelerator_options = accelerator_options
        return DocumentConverter(
            format_options={
                None: FormatOption(
                    backend=DoclingParseV4DocumentBackend,
                    pipeline_cls=SimplePipeline,
                    pipeline_options=pipeline_options,
                )
            }
        )

    def process(self) -> "str":

        if self.output_dir is not None:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Converting documents...Wait!")
        conv_results = self.convert()

        success_conv = 0
        failed_conv = 0

        for conv_result in conv_results:
            if conv_result.status == ConversionStatus.SUCCESS:
                success_conv += 1

                if self.verbose:
                    self.verbose_path = Path(f"{self.output_dir}/verbose/")
                    self.verbose_path.mkdir(parents=True, exist_ok=True)
                    _raw_path = Path(
                        f"{self.verbose_path}/raw_{conv_result.document.name}.json"
                    )
                    with _raw_path.open("w", encoding="utf-8") as _rp:
                        json.dump(
                            self.export(conv_result, export_to_dict=True),
                            _rp,
                            indent=4,
                            ensure_ascii=False,
                        )

                exp_result = self.export(conv_result)
                json_results = self.filter(exp_result)

                for i, _json_table in enumerate(json_results):
                    json_path = Path(
                        f"{self.output_dir}/updated_{conv_result.document.name}_{i}.json"
                    )
                    with json_path.open("w", encoding="utf-8") as fp:
                        json.dump(_json_table, fp, indent=4, ensure_ascii=False)
            else:
                logger.warning("Conversion failed!")
                failed_conv += 1

        return logger.info(f"Success: {success_conv}; Failed: {failed_conv}")

    def convert(self) -> Iterable[ConversionResult]:
        conv_results = self._config().convert_all(self.file_path)
        return conv_results

    def export(
        self, conv_result: ConversionResult, export_to_dict: bool = True
    ) -> Union[str, Dict[str, Any]]:
        if export_to_dict:
            exp_result = conv_result.document.export_to_dict()
        else:
            exp_result = conv_result.document.export_to_html()
        return exp_result

    def filter(self, exp_result: Union[str, Dict[str, Any]]) -> List[Dict[str, str]]:

        _tables = []

        for _table in exp_result["tables"]:

            _table_header = []
            _table_header_n = 0

            _col_headers = []
            _col_headers_n = 0

            _rows = []
            _n_col = int(_table["prov"][0]["bbox"]["r"])

            for _grid in _table["data"]["grid"]:
                for _cell in _grid:
                    if _cell["column_header"] and (_cell["col_span"] == _n_col):
                        _table_header.append(_cell["text"])
                        _table_header_n += 1

                    elif _cell["column_header"] and (_cell["col_span"] == 1):
                        _col_headers.append(_cell["text"])
                        _col_headers_n += 1

                    elif _table_header_n == _n_col and (_col_headers_n != _n_col):
                        _col_headers.append(_cell["text"])
                        _col_headers_n += 1

                    else:
                        _rows.append(_cell["text"])

            _table = {}
            _table_w_header = {}

            if len(_table_header) != 0:
                for i, _col_header in enumerate(_col_headers):
                    _table[_col_header] = _rows[i::_n_col]
                _table_w_header[_table_header[0]] = _table
                _tables.append(_table_w_header)
            else:
                for i, _col_header in enumerate(_col_headers):
                    _table[_col_header] = _rows[i::_n_col]
                _tables.append(_table)

        return _tables


def setup_logger() -> "logger":
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    logger.addHandler(console_handler)
    return logger


if __name__ == "__main__":

    logger = setup_logger()
    reader = Reader(file_path=Path("/data"), verbose=True)
    reader.process()
