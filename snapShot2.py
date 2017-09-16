import diskPhysical
import random

def writeBlock(block_no, write_data):
	diskPhysical.writePhysicalBlock(block_no, write_data)

def readBlock(block_no):
	diskPhysical.readPhysicalBlock(block_no)

def createDisk(id, num_blocks):
	if (diskPhysical.virtualDiskSize - diskPhysical.usedBlocks < num_blocks) or diskPhysical.diskMap.has_key(id):
		return "Error : Either no space or disk id already there"
	else:
		createPatch(id, num_blocks)

def createPatch(id, num_blocks):
	if not diskPhysical.diskMap.has_key(id):
		diskPhysical.diskMap[id] = diskPhysical.Disk(id, num_blocks)
	disk = diskPhysical.diskMap[id]
	# disk = diskMap[id] if (diskMap.has_key(id)) else Disk(id, num_blocks)
	l = [(n,i) for n,i in enumerate(diskPhysical.unoccupied) if i.num >= num_blocks]
	print "in create patch : ", str(id) + " " + str(num_blocks)
	diskPhysical.printPatchList(diskPhysical.unoccupied)
	if (len(l)==0):
		p = diskPhysical.unoccupied[-1]
		(disk.patches).append(p)
		diskPhysical.unoccupied.pop()
		diskPhysical.usedBlocks += p.num 
		createPatch(id,num_blocks-p.num)
	else:
		index = (l[0])[0]
		objBlockNo = (l[0])[1].blockNo
		objNum = (l[0])[1].num
		(disk.patches).append(diskPhysical.Patch(objBlockNo,num_blocks))
		if (objNum == num_blocks):
			diskPhysical.unoccupied.pop(index)
		else:
			currentvalue = objNum - num_blocks
			while index > 0 and diskPhysical.unoccupied[index-1].num > currentvalue:
				diskPhysical.unoccupied[index].blockNo = diskPhysical.unoccupied[index-1].blockNo
				diskPhysical.unoccupied[index].num = diskPhysical.unoccupied[index-1].num
				index -= 1
			diskPhysical.unoccupied[index].blockNo = objBlockNo + num_blocks
			diskPhysical.unoccupied[index].num = currentvalue
		diskPhysical.usedBlocks += num_blocks

def getVirtualDiskNo(diskPatches, block_no):
	total_blocks = 0
	i = 0
	while (diskPatches[i].num + total_blocks < block_no+1):
		total_blocks += diskPatches[i].num
		i += 1
	return diskPatches[i].blockNo + block_no - total_blocks

def readDiskBlock(id, block_no):
	if not diskPhysical.diskMap.has_key(id):
		raise "Error : Disk does not exist"
	disk = diskPhysical.diskMap[id]
	if disk.numBlocks < block_no+1:
		raise "Error : Invalid block number"
	# random no in 1 to 100.
	print "Reading disk block..."
	if random.randint(1, 100) < 50:
		# assuming replica always exists : ERROR?
		print "Read error!"
		if (len(diskPhysical.unoccupied)==0):
			raise "Error : Replica cannot be made"
		else:
			newReplicaBlockNo = diskPhysical.unoccupied[0].blockNo
			if (diskPhysical.unoccupied[0].num == 1):
				diskPhysical.unoccupied.pop(0)
			else:
				diskPhysical.unoccupied[0].num -= 1
				diskPhysical.unoccupied[0].blockNo += 1
			diskPhysical.usedBlocks += 1

			patches_new = []
			virt_original = getVirtualDiskNo(disk.patches, block_no)
			virt_replica = diskPhysical.getBlockReplica(virt_original)
			virt_new_replica = newReplicaBlockNo

			diskPhysical.setBlockReplica(virt_replica, virt_new_replica)
			diskPhysical.setBlockReplica(virt_new_replica, virt_replica)
			ans = diskPhysical.readPhysicalBlock(virt_replica)
			writeBlock(virt_new_replica, ans)
			
			newOriginal = diskPhysical.Patch(virt_replica, 1)
			newReplica = diskPhysical.Patch(virt_new_replica,1)
			for p in disk.patches:
				# TODO : CASE WHEN BLOCK 5 ME ERROR, THEN, BLOCK  ME ERROR.
				# if ((virt_replica < p.blockNo and virt_original < p.blockNo) or (virt_original > (p.blockNo+p.num) and virt_replica > (p.blockNo+p.num))):
				if ((virt_replica < p.blockNo or virt_replica >= (p.blockNo + p.num)) and (virt_original < p.blockNo or virt_original >= (p.blockNo + p.num))):
					patches_new.append(p)

				elif ((virt_original < p.blockNo or virt_original > (p.blockNo+p.num)) and p.blockNo <= virt_replica and virt_replica < p.blockNo+p.num):
					# only replica in this patch.
					if virt_replica > p.blockNo:
						left_patch = diskPhysical.Patch(p.blockNo, virt_replica - p.blockNo)
						patches_new.append(left_patch)
					patches_new.append(newReplica)
					if virt_replica < (p.blockNo + p.num - 1):
						right_patch = diskPhysical.Patch(virt_replica+1, p.num - (virt_replica - p.blockNo + 1))
						patches_new.append(right_patch)

				elif ((virt_replica > p.blockNo+p.num or virt_replica < p.blockNo) and p.blockNo <= virt_original and virt_original < p.blockNo+p.num):
					# only original in this patch.
					if virt_original > p.blockNo:
						left_patch = diskPhysical.Patch(p.blockNo, virt_original - p.blockNo)
						patches_new.append(left_patch)
					patches_new.append(newOriginal)
					if virt_original < (p.blockNo + p.num - 1):
						right_patch = diskPhysical.Patch(virt_original+1, p.num - (virt_original - p.blockNo + 1))
						patches_new.append(right_patch)

				else:
					if virt_original > p.blockNo:
						left_patch = diskPhysical.Patch(p.blockNo, virt_original - p.blockNo)
						patches_new.append(left_patch)
					patches_new.append(newOriginal)
					if virt_original < virt_replica-1:
						mid_patch = diskPhysical.Patch(virt_original+1, virt_replica - virt_original - 1)
						patches_new.append(mid_patch)
					patches_new.append(newReplica)
					if virt_replica < (p.blockNo + p.num - 1):
						right_patch = diskPhysical.Patch(virt_replica+1, p.num - (virt_replica - p.blockNo + 1))
						patches_new.append(right_patch)
			disk.patches = diskPhysical.mergePatches(patches_new)
			print "New patches : "
			for i in disk.patches:
				print str(i.blockNo) + " " + str(i.num)
	else:
		print "Old patches : "
		for i in disk.patches:
			print str(i.blockNo) + " " + str(i.num)
		ans = diskPhysical.readPhysicalBlock(getVirtualDiskNo(disk.patches, block_no))
	return ans	

def writeDiskBlock(id, block_no, write_data):
	if not diskPhysical.diskMap.has_key(id):
		raise "Error : Disk does not exist"
	disk = diskPhysical.diskMap[id]
	if disk.numBlocks < block_no+1:
		raise "Error : Invalid block number"
	print "Finding disk block..."
	virtual_block_no = getVirtualDiskNo(disk.patches, block_no)
	diskPhysical.writePhysicalBlock(virtual_block_no, write_data)
	if diskPhysical.getBlockReplica(virtual_block_no) == -1:
		delta = disk.numBlocks/2
		block_replica_disk = (block_no + delta) if block_no < delta else (block_no - delta)
		virtual_replica_block_no = getVirtualDiskNo(disk.patches, block_replica_disk)
		diskPhysical.setBlockReplica(virtual_block_no, virtual_replica_block_no)
		diskPhysical.setBlockReplica(virtual_replica_block_no, virtual_block_no)
	print "Virtual replica block no : ", str(diskPhysical.getBlockReplica(virtual_block_no))
	diskPhysical.writePhysicalBlock(diskPhysical.getBlockReplica(virtual_block_no), write_data)
	print "Written disk block..."	

def deleteDisk(id):
	if not diskPhysical.diskMap.has_key(id):
		raise "Error : Invalid disk id"
	disk = diskPhysical.diskMap[id]
	unoccupied = diskPhysical.unoccupied + disk.patches
	diskPhysical.printPatchList(unoccupied)
	unoccupied_sorted_index = sorted(unoccupied, key=lambda x: x.blockNo)
	diskPhysical.printPatchList(unoccupied_sorted_index)
	# unoccupied_new = []
	# current_patch = unoccupied_sorted_index[0]
	# for i in xrange(1,len(unoccupied_sorted_index)):
	# 	p = unoccupied_sorted_index[i]
	# 	if p.blockNo == current_patch.blockNo + current_patch.num:
	# 		current_patch.num += p.num
	# 	else:
	# 		unoccupied_new.append(current_patch)
	# 		current_patch = p
	# unoccupied_new.append(current_patch)
	# unoccupied = unoccupied_new
	unoccupied = diskPhysical.mergePatches(unoccupied_sorted_index)
	diskPhysical.unoccupied = sorted(unoccupied, key=lambda x: x.num)
	diskPhysical.usedBlocks -= disk.numBlocks
	diskPhysical.diskMap.pop(id)
	print "Deleted disk!"

def checkPoint(disk_id):
	disk = diskPhysical.diskMap[disk_id]
	disk.checkPointMap.append(len(disk.commandList))
	return len(disk.checkPointMap)-1

def rollBack(disk_id, checkpoint_id):
	# save checkpoint tk command List
	if not diskPhysical.diskMap.has_key(disk_id):
		raise "Error : Invalid disk id"
	disk = diskPhysical.diskMap[disk_id]
	print "Checkpoint id : ", checkpoint_id
	checkpoints = disk.checkPointMap[:(checkpoint_id)] # excluding the current one
	commands = disk.commandList[:(disk.checkPointMap[checkpoint_id])]
	print disk.checkPointMap
	# delete disk from diskMap
	deleteDisk(disk_id)
	# create new disk, exec all cmds
	for cmd in commands:
		if cmd[0] == "createDisk":
			createDisk(cmd[1], cmd[2])
			disk = diskPhysical.diskMap[disk_id]
		elif cmd[0] == "readDiskBlock":
			x = readDiskBlock(disk_id, cmd[1])
		else:
			writeDiskBlock(disk_id, cmd[1], cmd[2])
	disk.checkPointMap = checkpoints
	disk.commandList = commands

	print disk.commandList
	print disk.checkPointMap