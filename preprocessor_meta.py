# import numpy as np
# import torch
# from scipy.ndimage import median_filter
# import torch.nn.functional as F

# input shape torch.Size([8, 4, 1, 256, 256])
# output shape torch.Size([8, 1, 1, 256, 256])
# Input: RGB + NIR
# Target: 10-class label


# def process_train(self, x):
#     x['inputs'] = torch.squeeze(x['inputs'])
#     x['inputs'] = torch.nan_to_num(x['inputs'])
#     x['target'] = torch.squeeze(x['target'])
#     return x

import torch
import torch.nn.functional as F

class PreprocessorTemp:
    def median_filter_torch(self, x, kernel_size=3):
        """Applies a median filter using PyTorch's unfolding operation.
        Expected input shape: [batch, channels, height, width]
        """
        # Input is already 4D: [batch, channels, height, width]
        pad = kernel_size // 2
        x_padded = F.pad(x, (pad, pad, pad, pad), mode='reflect')  # Pad the spatial dimensions (H,W)
        
        # Unfold the spatial dimensions (H,W)
        unfolded = x_padded.unfold(2, kernel_size, 1).unfold(3, kernel_size, 1)
        
        # Apply median filter while preserving batch and channel dimensions
        # Reshape to [batch, channels, height, width, kernel_size*kernel_size]
        return torch.median(unfolded.contiguous().view(x.size(0), x.size(1), 
                                                     x.size(2), x.size(3), -1), 
                          dim=-1).values

    def process_train(self, x):
        x['inputs'] = torch.squeeze(x['inputs'])
        x['inputs'] = torch.nan_to_num(x['inputs'])
        x['inputs'] = self.median_filter_torch(x['inputs'])
        x['target'] = torch.squeeze(x['target'])
        return x


        


    
