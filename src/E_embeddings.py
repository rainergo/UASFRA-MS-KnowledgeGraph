import torch
from transformers import AutoTokenizer, AutoModel


class Embedder:

    def __init__(self, model_name: str = "bert-base-uncased", return_tensor: bool = False):
        self.tokenizer = AutoTokenizer.from_pretrained(pretrained_model_name_or_path=model_name)
        self.model = AutoModel.from_pretrained(pretrained_model_name_or_path=model_name,
                                               output_hidden_states=True)
        self.return_tensor: bool = return_tensor

    def tokenize_text(self, text: str, add_special_tokens: bool, padding: bool,
                      truncation: bool, return_tensors: str):
        return self.tokenizer.encode(text, return_tensors=return_tensors, add_special_tokens=add_special_tokens,
                                     max_length=512, truncation=truncation, padding=padding)

    def get_embedding(self, text: str, num_last_layers: int = 12, add_special_tokens: bool = True, padding: bool = True,
                      truncation: bool = True, return_tensors: str = "pt") -> list or torch.Tensor:
        tokenized_text = self.tokenize_text(text=text, add_special_tokens=add_special_tokens,
                                            truncation=truncation, padding=padding, return_tensors=return_tensors)
        with torch.no_grad():
            output = self.model(tokenized_text)
        # print(output.hidden_states[num_last_layers].size())
        # print('---------------------')
        """ The 'pooler_ouput' is a [1, 768]-dimensional vector (in 'bert-base-uncased') of the [CLS]-token 
            further processed by a Linear layer and a Tanh activation function representing the context of 
            the whole text. 'The 'last_hidden_state' is the [1, num_token_in_text, 768]-dimensional vector of the
            hidden state of the last layer and thus must be averaged to get to a dimension of [1, 768]: """
        # print('Dimension of stack is:', hidden_states_sum.shape)
        if num_last_layers > 0:
            # embedding = output.last_hidden_state.mean(dim=1)
            layers = [no for no in range(-num_last_layers, 0, 1)]
            embedding = torch.stack([output.hidden_states[i] for i in layers]).mean(dim=0).mean(dim=1)
            # print('Dimension of embedding is:', embedding.shape)
        else:
            embedding = output.pooler_output
            # print('Dimension of embedding is:', embedding.shape)

        if self.return_tensor:
            # Only for debugging and calculating cosine-similarity (see below):
            embedding_list: torch.Tensor = embedding
        else:
            # For calculating Graph-Embeddings:
            embedding_list: list = embedding.flatten().tolist()

        return embedding_list


if __name__ == '__main__':
    emb = Embedder(return_tensor=True)
    num_last_layers = 4
    pad = True
    dim = 1
    sent1 = """Adidas AG is a German multinational corporation, founded and headquartered in Herzogenaurach, Bavaria, that designs and manufactures shoes, clothing and accessories. It is the largest sportswear manufacturer in Europe, and the second largest in the world, after Nike. It is the holding company for the Adidas Group, which consists 8.33% stake of the football club Bayern München, and Runtastic, an Austrian fitness technology company. Adidas's revenue for 2018 was listed at €21.915 billion. The company was started by Adolf Dassler in his mother's house; he was joined by his elder brother Rudolf in 1924 under the name Gebrüder Dassler Schuhfabrik ("Dassler Brothers Shoe Factory"). Dassler assisted in the development of spiked running shoes (spikes) for multiple athletic events. To enhance the quality of spiked athletic footwear, he transitioned from a previous model of heavy metal spikes to utilising canvas and rubber. Dassler persuaded U.S. sprinter Jesse Owens to use his handmade spikes at the 1936 Summer Olympics. In 1949, following a breakdown in the relationship between the brothers, Adolf created Adidas and Rudolf established Puma, which became Adidas's business rival. The three stripes are Adidas's identity mark, having been used on the company's clothing and shoe designs as a marketing aid. The branding, which Adidas bought in 1952 from Finnish sports company Karhu Sports for the equivalent of €1,600 and two bottles of whiskey, became so successful that Dassler described Adidas as "The three stripes company"."""
    sent2 = """Puma SE is a German multinational corporation that designs and manufactures athletic and casual footwear, apparel and accessories, which is headquartered in Herzogenaurach, Bavaria, Germany. Puma is the third largest sportswear manufacturer in the world. The company was founded in 1948 by Rudolf Dassler. In 1924, Rudolf and his brother Adolf "Adi" Dassler had jointly formed the company Gebrüder Dassler Schuhfabrik (Dassler Brothers Shoe Factory). The relationship between the two brothers deteriorated until the two agreed to split in 1948, forming two separate entities, Adidas and Puma. Following the split, Rudolf originally registered the newly established company as Ruda (derived from Rudolf Dassler, as Adidas was based on Adi Dassler), but later changed the name to Puma. Puma's earliest logo consisted of a square and beast jumping through a D, which was registered, along with the company's name, in 1948. Puma's shoe and clothing designs feature the Puma logo and the distinctive "Formstrip" which was introduced in 1958."""
    sent3 = """RWE AG is a German multinational energy company headquartered in Essen. It generates and trades electricity in Asia-Pacific, Europe and the United States. The company is the world's number two in offshore wind power and Europe's third largest in renewable energy. In the 2020 Forbes Global 2000, RWE Group was ranked as the 297th -largest public company in the world. RWE confirmed in December 2015, that it would separate its renewable energy generation, power grid and retail operations into a separate company, Innogy SE, during 2016, and sell a 10% holding in the business through an initial public offering. The restructuring was caused by an effort to reduce the group's exposure to nuclear decommissioning costs, required due to a German government policy of closing all nuclear power stations by 2022. In July 2019, RWE's handling of the conflict with activists in the Hambach Forest were strongly criticized in the media. The company finally agreed to refrain from clearing the forest until autumn 2020. In July 2020, RWE completed a far-reaching asset swap deal with E.ON first announced in 2018, whereby the international renewable generation portfolio of E.ON and Innogy were transferred to RWE."""
    sent4 = """E.ON SE is a European electric utility company based in Essen, Germany. It runs one of the world's largest investor-owned electric utility service providers. The name comes from the Latin word aeon, from the Greek aion which means age. The company is a component of the Euro Stoxx 50 stock market index, DAX stock index and a member of the Dow Jones Global Titans 50 index. It operates in over 30 countries and has over 33 million customers. Its chief executive officer is Leonhard Birnbaum. E.ON was created in 2000 through the merger of VEBA and VIAG. In 2016, it separated its conventional power generation and energy trading operations into a new company, Uniper, while retaining retail, distribution and nuclear operations. E.ON sold its stake in Uniper through a stock market listing and sold the remaining stock to the Finnish utility Fortum. In March 2018, it was announced that E.ON would acquire the utility portion of renewable energy utility Innogy through a complex €43 billion asset swap deal between E.ON, Innogy and RWE. The deal was approved by the EU antitrust authorities in September 2019, with final execution taking place in July 2020. In 2019, E.ON became the first of the "Big Six" UK power companies to switch all of its British electricity customers entirely to renewable electricity. However the company still owns coal power in Turkey. In 2020, E.ON UK announced that it would be migrating customers over to a new subsidiary brand called E.ON Next. E.ON Next also has two million migrated customers from commercial energy firm npower Business Solutions and Powershop after acquiring both companies."""
    sent5 = """BASF SE is a German multinational chemical company and the largest chemical producer in the world. Its headquarters is located in Ludwigshafen, Germany. The BASF Group comprises subsidiaries and joint ventures in more than 80 countries and operates six integrated production sites and 390 other production sites in Europe, Asia, Australia, the Americas and Africa. BASF has customers in over 190 countries and supplies products to a wide variety of industries. Despite its size and global presence, BASF has received relatively little public attention since it abandoned the manufacture and sale of BASF-branded consumer electronics products in the 1990s. At the end of 2019, the company employed 117,628 people, with over 54,000 in Germany. In 2019, BASF posted sales of €59.3 billion and income from operations before special items of about €4.5 billion. Between 1990 and 2005, the company invested €5.6 billion in Asia, specifically in sites near Nanjing and Shanghai in China and Mangalore in India. BASF is listed on the Frankfurt Stock Exchange, London Stock Exchange, and Zurich Stock Exchange. The company delisted its ADR from the New York Stock Exchange in September 2007. The company is a component of the Euro Stoxx 50 stock market index."""
    res1 = emb.get_embedding(text=sent1, padding=pad, num_last_layers=num_last_layers)
    res2 = emb.get_embedding(text=sent2, padding=pad, num_last_layers=num_last_layers)
    res3 = emb.get_embedding(text=sent3, padding=pad, num_last_layers=num_last_layers)
    res4 = emb.get_embedding(text=sent4, padding=pad, num_last_layers=num_last_layers)
    res5 = emb.get_embedding(text=sent5, padding=pad, num_last_layers=num_last_layers)
    cos12 = torch.cosine_similarity(res1, res2)
    cos34 = torch.cosine_similarity(res3, res4)
    cos13 = torch.cosine_similarity(res1, res4)
    cos24 = torch.cosine_similarity(res2, res4)
    cos15 = torch.cosine_similarity(res1, res5)
    print('COS-SIM: Adidas and Puma:', cos12)
    print('COS-SIM: Adidas and BASF:', cos15)
    print('COS-SIM: Adidas and RWE', cos13)
    print('COS-SIM: EON and RWE', cos34)
    print('COS-SIM: Puma and EON', cos24)
    # print('length of embedding list', len(res1))
    # print('list:\n', res1)
