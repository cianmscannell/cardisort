import numpy as np
import pydicom
import os,sys
import pickle
import tensorflow.keras as tfk
from skimage.transform import resize

import cardisort_utils

M = 256
N = 256
def main(args):

    if len(args) < 2:
        print("Directories not specified.")
        return 1
    if len(args) == 2:
        input_dir = args[1]
        if 'cardisort' in input_dir.lower():
            return 1
        all_patient_items = os.listdir(input_dir)
        if len(all_patient_items) == 1:
            itm = all_patient_items[0]
            if os.path.isdir(itm):
                input_dir = os.path.join(input_dir, itm)

        front, back = os.path.split(input_dir)
        if len(back):
            output_dir = os.path.join(front, f"CardiSorted_{back}")
        else:
            output_dir = f"CardiSorted_{input_dir}"
    if len(args) == 3:
        input_dir = args[1]
        if 'cardisort' in input_dir.lower():
            return 1
        all_patient_items = os.listdir(input_dir)
        if len(all_patient_items) == 1:
            itm = all_patient_items[0]
            if os.path.isdir(itm):
                input_dir = os.path.join(input_dir, itm)

        output_dir = args[2]

    front, back = os.path.split(input_dir)
    if len(back):
        if back[0] == '_'or back[0] == '.':
            return 1
    else:
        if input_dir[0] == '_'or input_dir[0] == '.':
            return 1        

    cardisort_model = tfk.models.load_model('cardisort_model.ckpt')
    with open("seq_categories.pickle","rb") as pickle_in:
        seq_categories = pickle.load(pickle_in)
    with open("plane_categories.pickle","rb") as pickle_in:
        plane_categories = pickle.load(pickle_in)

    all_files = cardisort_utils.get_files(input_dir)

    dicom_ds = pydicom.read_file(all_files[0])
    the_manufacturer = dicom_ds.Manufacturer.lower()
    if 'philips' in the_manufacturer or 'ge' in the_manufacturer:
        this_order_patient_dict = cardisort_utils.get_philips_ge_dict(all_files)
    elif 'siemens' in the_manufacturer:
        this_order_patient_dict = cardisort_utils.get_siemens_dict(all_files)
    else:
        raise ValueError

    this_patient_dict_for_infer = cardisort_utils.get_inference_dict(this_order_patient_dict, M, N)
    series_counts = np.zeros((len(seq_categories),len(plane_categories)))
    for key in this_patient_dict_for_infer:
        out = cardisort_model(this_patient_dict_for_infer[key][np.newaxis,...])
        s = np.argmax(out[0].numpy())
        p = np.argmax(out[1].numpy())
        series_counts[s,p] += 1
        cardisort_utils.write_sorted(this_order_patient_dict[key],output_dir,seq_categories[s],plane_categories[p],series_counts[s,p])

    return 0

if __name__ == "__main__":
    main(sys.argv)
    sys.exit(0)    
