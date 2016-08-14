
class Shape(object):
    ##ACCESSORS##
    def __init__(self, min_height, max_height, stylus_width, flat = False):
        '''
        stylus width is needed to determine total length of shape list.
        each element in the list is a vertical level of the 3d object. Each
        level is then divided into a node tree based on if a triangle is to the 
        x axis horizontal left or right of the root triangle's x axis middle 
        point.
        if two triangles share the exact same middle point, which is unlikely, 
        that node's data becomes a list with both triangle objs in the list.
        
        This being the case, the run time for a triangle search becomes
        
        O(N,A) = 1
        
        Where A = Number of triangles in the same level as query
              N = Number of triangles that share the same x axis point
        '''    
        self.stylus_width = stylus_width
        self.data = []
        self.flat_data = []
        self.min_height = min_height
        self.max_height = max_height
	  #Flat Shape Triangle Variables#
        self.preliminary_height_min = None
        self.preliminary_height_max = None
        self.is_flat = flat
        if not flat:
            self._generate_list()
        else:
            self.num_levels = 0
            self.stylus_width = stylus_width
					
    def _generate_list(self):
        self.num_levels = int((self.max_height - \
        self.min_height)/self.stylus_width)
        for levels in range(0, self.num_levels):
            self.data.append(None)
            self.flat_data.append(None)    
    ##MODIFIERS##
    def add(self, new_face):

        cross_pts = []
        triangle_height_min = new_face.heightmin
        triangle_height_max = new_face.heightmax
        starting_height = int(triangle_height_min/self.stylus_width)
        ending_height = int(triangle_height_max/self.stylus_width)
        for levels in range(starting_height, ending_height):
            if new_face.flat == self.is_flat:
                if self.data[levels] is None:
                    self.data[levels] = {}
                cross_pts = new_face.get_cross_pts((levels*self.stylus_width))
                try:
                    self.data[levels][str(cross_pts.p1)].append(cross_pts)
                except KeyError:
                    self.data[levels][str(cross_pts.p1)] = [cross_pts]
                try:
                    self.data[levels][str(cross_pts.p2)].append(cross_pts)
                except KeyError:
                    self.data[levels][str(cross_pts.p2)] = [cross_pts]   

            else:
                if self.flat_data[levels] == None:
                    self.flat_data[levels] = []
                self.flat_data[levels].append(new_face)

    '''
    this data structure is recursive in a sense. if there are flat triangles
    in a level, a new Shape object will be created,  with the flat triangles
    in that level stored in that structure.
       
    Why?
       
     We already have the functions in place to translate triangle groups in two
    dimensions to lines for a motor system to follow. The two dimensions don't
    have to be x and y though, they can be z and x, or z and y. By keeping
    constant which dimensions we use for a flat level, we can treat it like
    a flat shape to print, but horizontally instead of vertically.
    '''
           
    #adds the node to its respective tree
    def get_max_min(self, unordered_faces):
        height_min = 0
        height_max = 0
        for new_face in unordered_faces:
            if new_face.lowp.height < height_min:
                height_min = new_face.lowp.height
            if new_face.highp.height > self.height_max:
                self.height_max = new_face.highp.height
        return height_min, height_max
    def _sort(self):
        self.min_height = self.preliminary_height_min
        self.max_height = self.preliminary_height_max
        for triangle in self.unordered_:
            self.add(triangle)
    def finish(self):
        for levels in range(len(self.data)):
            print('len data[levels]: ', len(self.data[levels].keys()))
            self.data[levels] = self.order(self.data[levels])
        for flat_levels in self.flat_data:
            flat_levels.finish()
    def order(self, points):
        links = {}
        links[str(points[points.keys()[0]][0].p1)] = \
        points[points.keys()[0]][0].p2
        first_point = points[points.keys()[0]][0].p1
        follow_pt = points[points.keys()[0]][0].p1
        next_pt = points[points.keys()[0]][0].p2
        counter = 0
        while True:
            counter += 1
            if counter == 100000:
                break
            #print('next pt: ', str(next_pt), 'first pt: ', str(first_point))
            
            if follow_pt == points[str(next_pt)][0].p1 or \
            follow_pt == points[str(next_pt)][0].p2:
                if points[str(next_pt)][1].p1 == next_pt:
                    links[str(next_pt)] = points[str(next_pt)][1].p2
                else:
                    links[str(next_pt)] = points[str(next_pt)][1].p1
            else:
                if points[str(next_pt)][0].p1 == next_pt:
                    links[str(next_pt)] = points[str(next_pt)][0].p2
                else:
                    links[str(next_pt)] = points[str(next_pt)][0].p1
            if links[str(next_pt)] == first_point:
                break
            follow_pt = next_pt
            next_pt = links[str(next_pt)]
        ordered_pts = []
        first_point = follow_pt
        next_pt = links[str(first_point)]
        while next_pt != first_point:
            ordered_pts.append(next_pt)
            follow_pt = next_pt
            next_pt = links[str(next_pt)]
        ordered_pts.append(first_point)
        return ordered_pts
    def divides_evenly(x, y):
        return not x%y
        
#point objects combined into face objects
class Line(object):
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2
    def __str__(self):
        return '{' + str(self.p1) + ' to ' + str(self.p2) + '}'
class Face(object):
    ##CONSTRUCTORS##
    def __init__(self, p1, p2, p3 = None):
        #if not default constructor, set points
        self.highp = None
        self.lowp = None
        self.midp = None
        if p3 != None:
            #finding highest and lowest z axis point
            self.zmax = max(p1.z, p2.z, p3.z)
            self.zmin = min(p1.z, p2.z, p3.z)
            if(self.zmax == self.zmin):
                self.flat = True
                '''
                shuffles the points so that the triangle can be used by the
                Face functions to find connecting lines
                '''
                p1_ = Points(p1.x, p1.y, p1.z)
                p1_.height = p1_.y
                p2_ = Points(p2.x, p2.y, p2.z)
                p2_.height = p2_.y
                p3_ = Points(p3.x, p3.y, p3.z)
                p3_.height = p3_.y
                self.heightmax = max(p1_.height, p2_.height, p3_.height)
                self.heightmin = min(p1_.height, p2_.height, p3_.height)
                self.point_sort(p1_, p2_, p3_)
            else: 
                self.flat = False
                self.heightmax = self.zmax
                self.heightmin = self.zmin
                self.point_sort(p1, p2, p3)
        else:
            print 'Error: too few points for certian inputted face. '
    ##MODIFIERS##
    #sorting points based on level on z axis
    def point_sort(self, p_1, p_2, p_3):
    #finding top and bottom points from zmax/min calculations
        if p_3.height == self.heightmax:
            if p_2.height == self.heightmin:
                self.highp = p_3
                self.midp = p_1
                self.lowp = p_2
            if p_1.height == self.heightmin:
                self.highp = p_3
                self.midp = p_2
                self.lowp = p_1
        elif p_2.height == self.heightmax:
            if p_3.height == self.heightmin:
                self.highp = p_2
                self.midp = p_1
                self.lowp = p_3
            if p_1.height == self.heightmin:
                self.highp = p_2
                self.midp = p_3
                self.lowp = p_1
        else:
            if p_3.height == self.heightmin:
                self.highp = p_1
                self.midp = p_2
                self.lowp = p_3
            if p_2.height == self.heightmin:
                self.highp = p_1
                self.midp = p_3
                self.lowp = p_2   
        self.tri_height = self.lowp.height
    def get_cross_pts(self, stylus_height):
        cross_pts = []
        dem_ratio = self.highp.height - self.tri_height
        num_ratio = stylus_height - self.tri_height
        #ratio is the percentage of how high the stylus is with respect to 
        #the given line connecting two points on a triangle
        ratio = num_ratio/dem_ratio
        #no matter what, we have to calculate the lowp to high p cross point
        
        #need to fix so it works with 1 dimenstional flat surface
        low_to_high_y = ratio*(self.highp.y - self.lowp.y) + self.lowp.y
        low_to_high_x = ratio*(self.highp.x - self.lowp.x) + self.lowp.x
        if not self.flat:
            cross_pts.append(Points(low_to_high_x, low_to_high_y, stylus_height))
        else:
            cross_pts.append(Points(low_to_high_x, stylus_height, self.lowp.z))      
        
        #if the stylus is above the middle point of the triangle, we need to
        #find the cross point between the middle and top point, if it is below
        #we need to find the cross point between the top and bottom point
            
        if self.midp.height > stylus_height and self.midp.height != \
        self.lowp.height:
            dem_ratio = self.midp.height - self.tri_height
            num_ratio = stylus_height - self.tri_height
            #ratio is the percentage of how high the stylus is with respect to 
            #the given line connecting two points on a triangle
            ratio = num_ratio/dem_ratio
            low_to_mid_y = ratio*(self.midp.y - self.lowp.y) + self.lowp.y
            low_to_mid_x = ratio*(self.midp.x - self.lowp.x) + self.lowp.x  
            if not self.flat:
                cross_pts.append(Points(low_to_mid_x, low_to_mid_y, stylus_height))
            else:
                cross_pts.append(Points(low_to_mid_x, stylus_height, self.lowp.z)) 
        else:
            dem_ratio = self.highp.height - self.midp.height
            num_ratio = stylus_height - self.midp.height
            #ratio is the percentage of how high the stylus is with respect to 
            #the given line connecting two points on a triangle
            ratio = num_ratio/dem_ratio 
            mid_to_high_y = ratio*(self.highp.y - self.midp.y) + self.midp.y
            mid_to_high_x = ratio*(self.highp.x - self.midp.x) + self.midp.x  
            if self.flat is False:
                cross_pts.append(Points(mid_to_high_x, mid_to_high_y, stylus_height))
            else:
                cross_pts.append(Points(mid_to_high_x, stylus_height, self.lowp.z)) 
        new_line = Line(cross_pts[0], cross_pts[1])
        return new_line
class Points(object):
    ##CONSTRUCTORS##
    def __init__(self, x, y, z):#constructor given all points
        self.x = float(x)
        self.y = float(y)
        self.z = float(z) 
        self.height = self.z
    def __str__(self):
        return '( ' + str(self.x) + ', ' + str(self.y) + ', ' + \
        str(self.z) + ' )'
    def __eq__(self, other):
        if self.x == other.x:
            if self.y == other.y:
                if self.z == other.z:
                    return True
        return False

def find_vertexes(file_input):
    #finding vertexes
    vertexes = []
    vertex = []
    for lines in open(file_input):
        if 'v ' in lines:
            lines = lines.strip('v').strip('\n').strip(' ')
            vertex = list(lines.split(' '))
            vertexes.append(Points(vertex[0], vertex[1], vertex[2]))
    return vertexes
#combine point instances in obj_vertexes to face instances
def find_faces(file_input, points):
    face = []#placeholder
    face_objs = []
    final_faces = []
    for lines in open(file_input):#finding face description in file
        if 'f' in lines and '#' not in lines:
            face = lines.strip('f').strip('\n').strip(' ')#stripping junk
            face = face.split(' ')#initial line split based on space delimeter
            for set_pts in range(0, len(face)):
                face[set_pts] = face[set_pts].split('/')#creating sublists with '/'
                face[set_pts] = int(face[set_pts][0])
                '''
                ^^^
                Replacing the element in face with the only needed data from
                the sublist created from face[faces] = face[faces].split('/')
                
                only first input needed, as
                that corresponds with which vertex makes up that third of the 
                triangle.
                [34//3, 23/2/1, 23//] -> [[34, , 3], [23,2,1], [12, , ,]]
                The other elements in the sublist are the normalcy and texture,
                which are unneeded. 
                This means after
                
                face[set_pts] = int(face[set_pts][0])
                
                we are left with [34, 23, 12]
                
                which corresepond with which points make up the face
                '''
            final_faces = [points[face[0]-1], points[face[1]-1], points[face[2]-1]]
            face_objs.append(Face(final_faces[0], final_faces[1], final_faces[2]))
    return face_objs
def print_to_blender(list_of_lists_of_pts):
    f = open('blender_input.txt', 'r')
    file_lines = f.readlines()
    f.close()
    f = open('blender_input.txt', 'w')
    skip_to_next_brkt = False
    for lines in file_lines:
        if skip_to_next_brkt == True:
            if lines == '          ]\n' or lines == '          )\n':
                skip_to_next_brkt = False
            continue
        if lines == '        Vertices = \\\n':
            f.write(write_verts(list_of_lists_of_pts))
            skip_to_next_brkt = True
        elif lines == '          (\n':
            f.write(write_edges(list_of_lists_of_pts))
            skip_to_next_brkt = True
        else:
            f.write(lines)
    f.close()

def write_verts(list_of_lists_of_pts):
    str_to_return = '        Vertices = \\\n'
    str_to_return += '          [\n'
    for levels in list_of_lists_of_pts:
        for pts in levels:
            str_to_return +=\
            '             mathutils.Vector(' + str(pts) + '),\n'
    str_to_return += '          ]\n'
    print(str_to_return)
    return str_to_return
def write_edges(list_of_lists_of_pts):
    str_to_return = '          (\n'
    str_to_return += '            Vertices,\n'
    counter = 0
    for levels in range(len(list_of_lists_of_pts)):
        starting_point = counter #used to complete level
        for pts in range(len(list_of_lists_of_pts[levels]) - 1):
            if counter == 0:
                str_to_return += '            [[' + str(counter) + ', ' + \
                str(counter + 1) + '],'  
            else:
                str_to_return += '            [' + str(counter) + ', ' +\
                str(counter + 1) + '],'
            if levels == len(list_of_lists_of_pts) - 1 and \
            pts == len(list_of_lists_of_pts[levels]) - 1:
                str_to_return += '],\n'
            else:
                str_to_return += '\n'
            counter += 1
        str_to_return += '            [' + str(counter) + ', ' +\
        str(starting_point) + '],'
        counter += 1
    str_to_return += '            []\n'
    str_to_return += '          )\n'
    return str_to_return
            
if __name__ == '__main__':
    input_file = "cube.txt" #raw_input("enter file name")
    obj_vertexes = find_vertexes(input_file)
    width_stylus = .035
    faces = find_faces(input_file, obj_vertexes)
    model = Shape(0, 20, 1.7)
    for face in range(len(faces)):
        print(faces[face].flat)
        model.add(faces[face])
    model.finish()
    for levels in model.data:
        for points in levels:
            print(points)
    print_to_blender(model.data)
    #once model is created, begin chaining level lines together.
    