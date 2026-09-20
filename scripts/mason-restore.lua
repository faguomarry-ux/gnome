-- Run with nvim -u NONE -l, so unrelated user plugin callbacks cannot end the process early.
vim.opt.rtp:prepend(vim.fn.expand('~/.local/share/nvim/lazy/mason.nvim'))
require('mason').setup()
local registry = require('mason-registry')
local packages = vim.json.decode(table.concat(vim.fn.readfile(vim.env.GNOME_MIGRATE_ROOT .. '/scripts/editor-tools.json'), '\n'))
local done, failed, pending = false, {}, 0
registry.refresh(function(success)
  if not success then table.insert(failed, 'registry refresh'); done = true; return end
  for _, name in ipairs(packages) do
    local ok, pkg = pcall(registry.get_package, name)
    if not ok then table.insert(failed, name .. ': not found')
    elseif pkg:is_installed() then print('[已安装] ' .. name)
    else
      pending = pending + 1
      print('[安装] ' .. name)
      pkg:install():once('closed', function()
        if not pkg:is_installed() then table.insert(failed, name) end
        pending = pending - 1
      end)
    end
  end
  done = true
end)
local completed = vim.wait(30 * 60 * 1000, function() return done and pending == 0 end, 200)
if not completed or #failed > 0 then
  print('[失败] Mason 安装超时或失败: ' .. table.concat(failed, ', '))
  vim.cmd('cquit 1')
end
print('[成功] Mason 工具全部就绪。')
