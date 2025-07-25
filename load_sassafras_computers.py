import time

from sassafras_funcs import  get_sass_computers
from snipe_funcs import  get_snipe_manufacturers, get_snipe_models, load_snipe_model


# hard coding display category ID;


# https://www.sassafras.com/hrl/ksp-api.html#tag/Overview
# https://snipe-it.readme.io/reference/api-overview

snipe_manufacturers = get_snipe_manufacturers()

category_id = 31
snipe_models = get_snipe_models(category_id)
(sass_manufacturers, sass_models, sass_computers) = get_sass_computers('Laptop', category_id )

category_id = 18  
snipe_models |=  get_snipe_models(category_id)
(manufacturers, models, computers) = get_sass_computers('Standard', category_id )
sass_manufacturers |= manufacturers
sass_models |= models
sass_computers |= computers

category_id = 15  
snipe_models |=  get_snipe_models(category_id)
(manufacturers, models, computers) = get_sass_computers('Virtual', category_id )
sass_manufacturers |= manufacturers
sass_models |= models
sass_computers |= computers


print("--------------\nLoading New Manufacturers")
for manufacturer in sass_manufacturers:
  if not manufacturer in snipe_manufacturers:
     load_snipe_manufacturer(manufacturer)


print("--------------\nLoading New Models")
for model in sass_models:

   (manufacturer, category_id) = sass_models[model]
   snipe_manufacturer_id = snipe_manufacturers[manufacturer]

   if not model in snipe_models:
     #print(f"load_snipe_model({snipe_manufacturer_id}, {category_id}, {manufacturer}, {model}, {model})")
     load_snipe_model(snipe_manufacturer_id, category_id, manufacturer, model, model)
     time.sleep(1)








