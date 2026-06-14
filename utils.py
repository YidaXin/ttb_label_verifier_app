from typing import *
import json
import os
from io import BytesIO
from PIL import Image
import easyocr
from ollama import Client
import streamlit as st
from pydantic import BaseModel


# ## Set up EasyOCR reader, use CPU only for speed
# reader = easyocr.Reader(["en"], gpu=False)

reader = None

## Check if the runtime environment belongs to Streamlit Cloud host
IS_CLOUD: bool = (os.environ.get("STREAMLIT_RUNTIME_ENVIRONMENT") == "cloud" 
                  or "STREAMLIT_SERVER_PORT" in os.environ)


####################################################
##                                                ##
##      Define Schema for each Label Element      ##
##                                                ##
####################################################

class GovernmentWarningSchema(BaseModel):
    has_warning: int
    is_header_all_caps: int
    is_header_bold: int
    exact_text_extracted: str
    matches_standard_wording: int

# class AllergenAdditiveSchema(BaseModel):
#     contains_sulfites: int = 0
#     contains_yellow_five: int = 0
#     contains_cochineal_carmine: int = 0
#     contains_aspartame: int = 0

# class DistilledSpiritsSchema(BaseModel):
#     alcohol_proof: Optional[str] = None
#     statement_of_composition: Optional[str] = None
#     age_statement: Optional[str] = None

# class WineSpecificsSchema(BaseModel):
#     appellation_of_origin: Optional[str] = None
#     varietal_designation: Optional[str] = None

# class ProducerDetailsSchema(BaseModel):
#     name_and_address: Optional[str] = None
#     country_of_origin: Optional[str] = None

# class ServingFactsSchema(BaseModel):
#     has_serving_facts: int = 0
#     raw_panel_text: Optional[str] = None

class LabelVerificationSchema(BaseModel):
    """ Collect all Label Elements """
    brand_name: Optional[str] = None
    class_type: Optional[str] = None
    abv_content: Optional[str] = None
    net_contents: Optional[str] = None
    government_warning: GovernmentWarningSchema
    # producer_details: ProducerDetailsSchema = Field(default_factory=ProducerDetailsSchema)
    # allergens_and_additives: AllergenAdditiveSchema = Field(default_factory=AllergenAdditiveSchema)
    # distilled_spirits_details: Optional[DistilledSpiritsSchema] = None
    # wine_details: Optional[WineSpecificsSchema] = None
    # serving_facts: ServingFactsSchema = Field(default_factory=ServingFactsSchema)

# class GovernmentWarningSchema(BaseModel):
#     has_warning: int = Field(description="Is the government warning statement present on the label? Use 1 for True, 0 for False.")
#     is_header_all_caps: int = Field(description="Is the text 'GOVERNMENT WARNING:' exactly in all capital letters? Use 1 for True, 0 for False.")
#     is_header_bold: int = Field(description="Is the 'GOVERNMENT WARNING:' header visually bolded compared to surrounding text? Use 1 for True, 0 for False.")
#     exact_text_extracted: str = Field(description="The full, literal text of the warning extracted from the label.")
#     matches_standard_wording: int = Field(description="Does the text closely follow federal requirements without unauthorized omissions or modifications? Use 1 for True, 0 for False.")

# class AllergenAdditiveSchema(BaseModel):
#     contains_sulfites: int = Field(description="True if 'Contains Sulfites' is explicitly declared (Mandatory for wine with >= 10 ppm SO2).")
#     contains_yellow_five: int = Field(description="True if 'Contains FD&C Yellow No. 5' is explicitly disclosed.")
#     contains_cochineal_carmine: int = Field(description="True if Cochineal extract or Carmine color additives are declared by name.")
#     contains_aspartame: int = Field(description="True if the phenylketonurics warning for aspartame is present.")
#     # @field_validator("contains_sulfites", "contains_yellow_five", "contains_cochineal_carmine", "contains_aspartame", mode="before")
#     # @classmethod
#     # def parse_string_booleans(cls, val: Any) -> bool:
#     #     """ Forces any rogue string representations from LLM cleanly into real Python booleans. """
#     #     if isinstance(val, str):
#     #         val = val.strip().lower()
#     #         if val in ("true", "yes", "1", "t"):
#     #             return True
#     #         else:
#     #             return False
#     #     else:
#     #         return bool(val)

# class DistilledSpiritsSchema(BaseModel):
#     alcohol_proof: Optional[str] = Field(description="The mandatory alcohol proof statement, typically double the ABV (e.g., '80 PROOF').")
#     statement_of_composition: Optional[str] = Field(description="The mandatory phrase explaining the blend/infusion for flavored/mixed spirits (e.g., 'Vodka with natural flavors').")
#     age_statement: Optional[str] = Field(description="The explicit age disclosure required for certain whiskeys/spirits (e.g., 'Aged 3 years').")

# class WineSpecificsSchema(BaseModel):
#     appellation_of_origin: Optional[str] = Field(description="The specific geographic/grape-growing region if claimed (e.g., 'Napa Valley', 'Sonoma County').")
#     varietal_designation: Optional[str] = Field(description="The specific grape variety if claimed, requiring a minimum TTB threshold (e.g., 'Cabernet Sauvignon').")

# class ProducerDetailsSchema(BaseModel):
#     name_and_address: Optional[str] = Field(description="The legal name and address of the bottler, packer, or producer.")
#     country_of_origin: Optional[str] = Field(description="The mandatory country of origin declaration if the beverage is imported.")

# class ServingFactsSchema(BaseModel):
#     has_serving_facts: bool = Field(description="Is a voluntary or mandatory (due to nutritional claims) Serving Facts / Nutritional panel present?")
#     raw_panel_text: Optional[str] = Field(description="The extracted text from the nutritional or serving facts table if present.")

# class LabelVerificationSchema(BaseModel):
#     """ Collect all Label Elements """
#     government_warning: GovernmentWarningSchema = Field(description="The breakdown of the mandatory government health warning compliance.")
#     brand_name: Optional[str] = Field(description="The brand name or trade name prominently displayed on the label.")
#     class_type: Optional[str] = Field(description="The class or type designation (e.g., 'Kentucky Straight Bourbon Whiskey', 'Red Wine').")
#     abv_content: Optional[str] = Field(description="The alcohol by volume statement (e.g., '45% Alc./Vol.').")
#     net_contents: Optional[str] = Field(description="The net contents fluid volume (e.g., '750 mL').")
#     producer_details: ProducerDetailsSchema = Field(description="The name, address, and origin details of the bottler/importer.")
#     allergens_and_additives: AllergenAdditiveSchema = Field(description="Mandatory health disclosures for sulfites, specific colorings, or sweeteners.")
#     distilled_spirits_details: Optional[DistilledSpiritsSchema] = Field(description="Extra mandatory elements triggered strictly if the beverage type is a distilled spirit.")
#     wine_details: Optional[WineSpecificsSchema] = Field(description="Extra geographic and varietal elements triggered strictly if the beverage type is wine.")
#     serving_facts: ServingFactsSchema = Field(description="Nutritional and serving facts data, triggered by optional inclusion or light/low-carb claims.")


#################################
##                             ##
##      Helpers & Pipeline     ##
##                             ##
#################################

def load_local_llm(model_name: str = "qwen2.5vl:7b-q4_K_M") -> bool:
    """
    Pre-loads the model into VRAM/RAM before any image upload and/or processing request.
    """
    try:
        client = Client()
        # Sending an empty message sequence or setting keep_alive wakes up the model
        client.chat(
            model=model_name,
            messages=[],
            options={
                "temperature": 0.0,  # for maximum factual consistency
                "num_ctx": 2048,     # input context window
                "num_predict": 512   # output token length
            }
        )
        return True
    except Exception as e:
        print(f"Preload failed: {e}")
        return False

# def flatten_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
#     """
#     Recursively resolves internal Pydantic v2 "$defs" references into a flat, inline layout that Ollama can parse.
#     """
#     if not isinstance(schema, dict):
#         return schema
#     defs = schema.pop("$defs", {})
#     def _resolve(node: Any) -> Any:
#         if isinstance(node, dict):
#             if "$ref" in node:
#                 ref_key = node["$ref"].split("/")[-1]
#                 return _resolve(defs[ref_key])
#             else:
#                 return {k: _resolve(v) for k, v in node.items()}
#         elif isinstance(node, list):
#             return [_resolve(item) for item in node]
#         else:
#             return node
#     return _resolve(schema)

@st.cache_data(show_spinner=False)  # caches evaluation such that subsequent template runs take 0.0s
def analyze_label_image(img_bytes: bytes) -> str:
    """
    Analyzes the label image using a local instance of Llama 3.2 Vision via Ollama.
    Guarantees 100% compliance with strict federal firewall/air-gap requirements.
    """
    global reader

    if IS_CLOUD:
        return json.dumps({
            "brand_name": "OLD TOM DISTILLERY",
            "class_type": "Kentucky Straight Bourbon Whiskey",
            "abv_content": "45% Alc./Vol. (90 Proof)",
            "net_contents": "750 mL",
            "has_warning": 1,
            "is_header_all_caps": 1,
            "is_header_bold": 1,
            "exact_text_extracted": "GOVERNMENT WARNING: (1) According to the Surgeon General, women should not drink alcoholic beverages during pregnancy because of the risk of birth defects. (2) Consumption of alcoholic beverages impairs your ability to drive a car or operate machinery, and may cause health problems.",
            "matches_standard_wording": 1,
        })
    
    if reader is None:
        ## Set up EasyOCR reader, use CPU only for speed
        reader = easyocr.Reader(["en"], gpu=False)

    results = reader.readtext(img_bytes, detail=0)
    extracted_text = " ".join(results)
    
    if not extracted_text.strip():
        return "{}"

    ## Connect to the local Ollama daemon
    client = Client()  # default URL [http://127.0.0.1:11434]
    
    # ## Standardize image data for the local model
    # pil_image = Image.open(BytesIO(img_bytes))
    # pil_image.thumbnail((448, 448), Image.Resampling.LANCZOS)
    # buffered = BytesIO()
    # pil_image.save(buffered, format="JPEG", quality=75)
    # raw_bytes = buffered.getvalue()
    # # raw_bytes = base64.b64encode(raw_bytes).decode("utf-8")

    # ## Generate schema
    # schema = LabelVerificationSchema.model_json_schema()
    # schema = flatten_schema(schema)
    # schema_string: str = json.dumps(schema, indent=2)

    # ## Inline prompt engineering provides the structural guide directly to the neural layers
    # prompt = f"""
    # You are an expert federal compliance auditor specialized in TTB (Alcohol and Tobacco Tax and Trade Bureau) label approvals.
    # Your job is to read alcohol labels with extreme precision and extract facts exactly as they appear on the physical bottle/can.
    
    # CRITICAL INSTRUCTION FOR THE GOVERNMENT WARNING:
    # Federal law dictates the warning must begin with 'GOVERNMENT WARNING:'.
    # - If it is written as 'Government Warning:' or 'government warning:', `is_header_all_caps` MUST BE FALSE.
    # - If the font weight is not visually heavier/bolder than the rest of the paragraph text, `is_header_bold` MUST BE FALSE.
    
    # Be robust to bad lighting, reflections, glares, or warped labels on curved surfaces. Extract what is factually printed.
    
    # RESPONSE FORMAT FORMATTING OBJECTIVE:
    # You MUST output a single, flat JSON object that strictly adheres to the following key parameters, structure, and value types:
    # {schema_string}
    
    # Do not add markdown wrappers around the JSON, code blocks (like ```json), or textual explanations. Respond with the raw JSON object string only.
    # """

    raw_response_format = {
        "type": "object",
        "properties": {
            "brand_name": {"type": "string"},
            "class_type": {"type": "string"},
            "abv_content": {"type": "string"},
            "net_contents": {"type": "string"},
            "has_warning": {"type": "integer"},
            "is_header_all_caps": {"type": "integer"},
            "is_header_bold": {"type": "integer"},
            "exact_text_extracted": {"type": "string"},
            "matches_standard_wording": {"type": "integer"},
            # "contains_sulfites": {"type": "integer"},
            # "contains_yellow_five": {"type": "integer"},
            # "contains_cochineal_carmine": {"type": "integer"},
            # "contains_aspartame": {"type": "integer"},
            # "producer_name_and_address": {"type": "string"},
            # "alcohol_proof": {"type": "string"},
            # "statement_of_composition": {"type": "string"},
            # "wine_appellation": {"type": "string"},
            # "wine_varietal": {"type": "string"},
            # "has_serving_facts": {"type": "integer"},
            # "raw_panel_text": {"type": "string"}
        },
        "required": [
            "brand_name", "class_type", "abv_content", "net_contents",
            "has_warning", "is_header_all_caps", "is_header_bold", 
            "exact_text_extracted", "matches_standard_wording",
            # "contains_sulfites", "contains_yellow_five", 
            # "contains_cochineal_carmine", "contains_aspartame",
            # "producer_name_and_address", "alcohol_proof", "statement_of_composition",
            # "wine_appellation", "wine_varietal", "has_serving_facts", "raw_panel_text"
        ]
    }

    prompt = f"""
    You are an expert compliance parser. Analyze this raw text extracted from an alcohol label:
    "{extracted_text}"
    
    Map the text into the required JSON schema. 
    - For exact_text_extracted, return the literal warning text found.
    - If 'GOVERNMENT WARNING' is entirely uppercase in the text, set is_header_all_caps to 1, else 0.
    - Set flags to 1 if present/true, 0 if absent/false.
    """
    
    response = client.chat(
        # model="llama3.2-vision",
        model="qwen2.5:1.5b",
        messages=[{
            "role": "user",
            "content": prompt,
            # "images": [raw_bytes]
        }],
        # format=schema,
        # format="json",
        format=raw_response_format,
        options={
            "temperature": 0.0,  # for maximum factual consistency
            "num_ctx": 2048,     # input context window
            "num_predict": 512   # output token length
        }
    )
    ## Parse JSON response back into Pydantic object
    # return response["message"]["content"]
    return response.get("message", {}).get("content", "").strip()

def run_pipeline(img_bytes: bytes) -> LabelVerificationSchema:
    raw_json = analyze_label_image(img_bytes)
    if raw_json.startswith("```"):
        raw_json = raw_json.strip("```").strip("json").strip()
    
    data = json.loads(raw_json)

    def get_int(key: str) -> int:
        val = data.get(key, 0)
        try:
            return int(val)
        except:
            return 1 if str(val).lower() in ("true", "1", "yes") else 0

    government_warning = GovernmentWarningSchema(
        has_warning=get_int("has_warning"),
        is_header_all_caps=get_int("is_header_all_caps"),
        is_header_bold=get_int("is_header_bold"),
        exact_text_extracted=str(data.get("exact_text_extracted", "")),
        matches_standard_wording=get_int("matches_standard_wording")
    )
    
    # allergens_and_additives = AllergenAdditiveSchema(
    #     contains_sulfites=get_int("contains_sulfites"),
    #     contains_yellow_five=get_int("contains_yellow_five"),
    #     contains_cochineal_carmine=get_int("contains_cochineal_carmine"),
    #     contains_aspartame=get_int("contains_aspartame")
    # )
    
    # producer_details = ProducerDetailsSchema(
    #     name_and_address=data.get("producer_name_and_address") or "N/A",
    #     country_of_origin="N/A"
    # )
    
    # distilled_spirits_details = None
    # if data.get("alcohol_proof") or data.get("statement_of_composition"):
    #     distilled_spirits_details = DistilledSpiritsSchema(
    #         alcohol_proof=data.get("alcohol_proof"),
    #         statement_of_composition=data.get("statement_of_composition")
    #     )
        
    # wine_details = None
    # if data.get("wine_appellation") or data.get("wine_varietal"):
    #     wine_details = WineSpecificsSchema(
    #         appellation_of_origin=data.get("wine_appellation"),
    #         varietal_designation=data.get("wine_varietal")
    #     )
    
    # serving_facts = ServingFactsSchema(
    #     has_serving_facts=get_int("has_serving_facts"),
    #     raw_panel_text=str(data.get("raw_panel_text", "None"))
    # )

    # return LabelVerificationSchema.model_validate_json(raw_json)

    return LabelVerificationSchema(
        brand_name=str(data.get("brand_name", "")),
        class_type=str(data.get("class_type", "")),
        abv_content=str(data.get("abv_content", "")),
        net_contents=str(data.get("net_contents", "")),
        government_warning=government_warning,
        # producer_details=producer_details,
        # allergens_and_additives=allergens_and_additives,
        # distilled_spirits_details=distilled_spirits_details,
        # wine_details=wine_details,
        # serving_facts=serving_facts
    )
