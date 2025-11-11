import numpy as np
import torch
from torch.nn import functional as F
from torch.nn import Module

from torch.optim import Adam, AdamW, SGD
from torch.optim.lr_scheduler import ReduceLROnPlateau
from tqdm.notebook import tqdm
import time
import random
from torch.cuda.amp import autocast, GradScaler
import torch.onnx
from sklearn.metrics import confusion_matrix, precision_score, recall_score, f1_score





def val_unet_clf(model, preprocessor, train_loader, val_loader, test_loader, optimizer, num_epochs, device, weights = False):
    scaler = GradScaler()
    scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5, verbose=True)
    
    if weights == False: 
        loss_fn = torch.nn.CrossEntropyLoss()
    else:
        #class_weights = torch.ones(8, device=device)
        class_weights = torch.tensor([0, 5.5017, 0.5266, 1.1916, 0.4896, 0.9684, 4.7681, 0.5905], device=device)
        #class_weights[0] = 0
        # class_weights[1] = 1.3
        loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights)
    
    best_val_loss = float('inf')
    consecutive_increases = 0
    patience = 15
    
    for epoch in range(num_epochs):
        model.train()
        model.to(device)
        epoch_loss = 0.0
        for data in tqdm(train_loader, leave=False):
            data = preprocessor.process_train(data)
            inputs, target = data['inputs'].to(device), data['target'].long().to(device)  
            with torch.amp.autocast('cuda'):
                outputs = model(inputs)
                loss = loss_fn(outputs, target)
            optimizer.zero_grad()
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            epoch_loss += loss.item()
        epoch_loss /= len(train_loader)
        print(f'Epoch [{epoch+1}/{num_epochs}], Train Loss: {epoch_loss:.4f}')
        
        # Validation step
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for data in tqdm(val_loader, leave=False):
                data = preprocessor.process_train(data)
                inputs, target = data['inputs'].to(device), data['target'].long().to(device)
                with torch.amp.autocast('cuda'):
                    outputs = model(inputs)
                    loss = loss_fn(outputs, target)
                val_loss += loss.item()
        val_loss /= len(val_loader)
        print(f'Epoch [{epoch+1}/{num_epochs}], Validation Loss: {val_loss:.4f}')
        
        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict().copy()
            consecutive_increases = 0
            print(f'New best model saved with validation loss: {best_val_loss:.4f}')
        else:
            consecutive_increases += 1
            
        if consecutive_increases >= patience:
            print(f'Early stopping triggered after {epoch+1} epochs')
            break
        
        scheduler.step(val_loss)
    
    # Test phase
    # Load the best model before testing 
    model.load_state_dict(best_model_state)
    print(f'Loaded best model with validation loss: {best_val_loss:.4f}')
    
    model.eval()
    optimizer.zero_grad()
    model.to(device)
    test_loss = 0.0
    total_samples = 0
    all_inputs = []
    all_targets = []
    all_predictions = []
    with torch.no_grad():
        with torch.autocast(device_type='cuda', dtype=torch.float16):
            for data in tqdm(test_loader, leave=False):
                data = preprocessor.process_train(data)
                inputs, target = data['inputs'].to(device), data['target'].long().to(device)
                outputs = model(inputs)
                loss = loss_fn(outputs, target)
                test_loss += loss.item()
                total_samples += target.numel()
                probs = F.softmax(outputs, dim=1)
                predicted_classes = torch.argmax(probs, dim=1)
                all_inputs.append(inputs[1])
                all_targets.append(target[1])
                all_predictions.append(predicted_classes[1])
    
    return all_inputs, all_predictions, all_targets





def train_deeplabv3(model, preprocessor, train_loader, val_loader, test_loader, optimizer, num_epochs, device, weights=False):
    scaler = GradScaler()
    scheduler = ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=5, verbose=True)
    
    if weights == False:
        loss_fn = torch.nn.CrossEntropyLoss()
    else:
        class_weights = torch.tensor([0, 7.4524, 0.5512, 1.8861, 0.5153, 1.0477, 5.3341, 0.6951], device=device)
        loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights)
    
    best_val_loss = float('inf')
    consecutive_increases = 0
    patience = 8
    
    for epoch in range(num_epochs):
        model.train()
        model.to(device)
        epoch_loss = 0.0
        for data in tqdm(train_loader, leave=False):
            data = preprocessor.process_train(data)
            inputs, target = data['inputs'].to(device), data['target'].long().to(device)
            
            # Ensure input is in the correct format (B, C, H, W)
            if len(inputs.shape) == 3:
                inputs = inputs.unsqueeze(0)
            
            with torch.amp.autocast('cuda'):
                outputs = model(inputs)
                loss = loss_fn(outputs, target)
                
            optimizer.zero_grad()
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            epoch_loss += loss.item()
            
        epoch_loss /= len(train_loader)
        print(f'Epoch [{epoch+1}/{num_epochs}], Train Loss: {epoch_loss:.4f}')
        
        # Validation step
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for data in tqdm(val_loader, leave=False):
                data = preprocessor.process_train(data)
                inputs, target = data['inputs'].to(device), data['target'].long().to(device)
                
                if len(inputs.shape) == 3:
                    inputs = inputs.unsqueeze(0)
                    
                with torch.amp.autocast('cuda'):
                    outputs = model(inputs)
                    loss = loss_fn(outputs, target)
                val_loss += loss.item()
                
        val_loss /= len(val_loader)
        print(f'Epoch [{epoch+1}/{num_epochs}], Validation Loss: {val_loss:.4f}')
        
        # Early stopping check
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_state = model.state_dict().copy()
            consecutive_increases = 0
            print(f'New best model saved with validation loss: {best_val_loss:.4f}')
        else:
            consecutive_increases += 1
            
        if consecutive_increases >= patience:
            print(f'Early stopping triggered after {epoch+1} epochs')
            break
            
        scheduler.step(val_loss)
    
    # Test phase
    model.load_state_dict(best_model_state)
    print(f'Loaded best model with validation loss: {best_val_loss:.4f}')
    
    model.eval()
    optimizer.zero_grad()
    model.to(device)
    test_loss = 0.0
    all_inputs = []
    all_targets = []
    all_predictions = []
    
    with torch.no_grad():
        with torch.autocast(device_type='cuda', dtype=torch.float16):
            for data in tqdm(test_loader, leave=False):
                data = preprocessor.process_train(data)
                inputs, target = data['inputs'].to(device), data['target'].long().to(device)
                
                if len(inputs.shape) == 3:
                    inputs = inputs.unsqueeze(0)
                    
                outputs = model(inputs)
                loss = loss_fn(outputs, target)
                test_loss += loss.item()
                
                probs = F.softmax(outputs, dim=1)
                predicted_classes = torch.argmax(probs, dim=1)
                
                all_inputs.append(inputs[0] if inputs.shape[0] == 1 else inputs)
                all_targets.append(target)
                all_predictions.append(predicted_classes)
    
    return all_inputs, all_predictions, all_targets






    


