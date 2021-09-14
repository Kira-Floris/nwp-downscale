import torch
import torch.nn.functional as F

## Generator loss terms

def gen_wasserstein(disc_fake):
    return -torch.mean(disc_fake)

def gen_logistic_nonsaturating(disc_fake):
    return torch.mean(F.softplus(-disc_fake))

def ens_mean_L1_weighted(fake, real):
    mean_fake = torch.mean(fake, dim=0)
    diff = mean_fake - real
    def weight_diff(y):
        return torch.clamp(y+1, min=24)
    clipped = weight_diff(real)
    weighted_diff = diff * clipped
    l = (1/real.numel()) * torch.linalg.norm(weighted_diff.reshape(-1), 1)
    return l

    

## Discriminator loss terms
def disc_wasserstein(disc_real, disc_fake):
    return -(torch.mean(disc_real) - torch.mean(disc_fake))

def disc_hinge(disc_real, disc_fake):
    return torch.mean(F.relu(1-disc_real)) + torch.mean(F.relu(1+disc_fake))

def gradient_penalty(discriminator, condition, real, fake, device):
    batch_size, C, H, W = real.shape
    epsilon = torch.rand((batch_size, 1, 1, 1), device=device).repeat(1,C,H,W)
    interpolated_images = real*epsilon + fake*(1-epsilon)
    interpolated_images.requires_grad = True
    mixed_scores = discriminator(condition, interpolated_images)

    gradient = torch.autograd.grad(
                inputs=interpolated_images,
                outputs=mixed_scores, 
                grad_outputs = torch.ones_like(mixed_scores), 
                create_graph=True, 
                retain_graph = True)[0]

    gradient = gradient.view(gradient.shape[0], -1)
    gradient_norm = gradient.norm(2, dim=1)
    gradient_penalty = torch.mean((gradient_norm - 1)**2)
    return gradient_penalty

